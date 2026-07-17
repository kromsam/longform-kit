type Json = Record<string, unknown>;

function dirname(path: string): string {
  const normalized = path.replace(/\/+$/, "");
  const index = normalized.lastIndexOf("/");
  return index <= 0 ? "/" : normalized.slice(0, index);
}

function join(...parts: string[]): string {
  return parts.join("/").replace(/\/+/g, "/");
}

function relative(base: string, path: string): string {
  return path.startsWith(`${base}/`) ? path.slice(base.length + 1) : path;
}

const scriptPath = decodeURIComponent(new URL(import.meta.url).pathname);
const scriptsDir = dirname(scriptPath);
const projectDir = dirname(scriptsDir);
const quarto = Deno.env.get("LONGFORM_QUARTO") || "quarto";
const homeAdapterPath = join(projectDir, "index.md");
const homeAdapter = "{{< include document/front-matter.md >}}\n";
// Author-owned manuscript metadata merged into the config via metadata-files.
// These are the only non-Markdown files allowed at the top of document/:
// metadata.yml holds title/author/date/language and chapters.yml the chapter
// list.
const manuscriptMetadataFiles = new Set(["metadata.yml", "chapters.yml"]);
const manuscriptMetadataList = [...manuscriptMetadataFiles].join(", ");

async function run(
  command: string,
  args: string[],
  options: {
    cwd?: string;
    stdout?: "inherit" | "piped";
    stderr?: "inherit" | "piped";
  } = {},
) {
  const result = await new Deno.Command(command, {
    args,
    cwd: options.cwd || projectDir,
    stdout: options.stdout || "piped",
    stderr: options.stderr || "piped",
  }).output();
  if (!result.success) {
    const error = options.stderr === "inherit"
      ? ""
      : new TextDecoder().decode(result.stderr).trim();
    throw new Error(error || `${command} exited with ${result.code}`);
  }
  return options.stdout === "inherit"
    ? ""
    : new TextDecoder().decode(result.stdout);
}

async function inspect(): Promise<Json> {
  return JSON.parse(await run(quarto, ["inspect"])) as Json;
}

function object(value: unknown): Json {
  return value && typeof value === "object" && !Array.isArray(value)
    ? value as Json
    : {};
}

function strings(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item) => typeof item === "string")
    : [];
}

function configFrom(data: Json): Json {
  return object(data.config);
}

function chapterFiles(config: Json): string[] {
  const files = strings(object(config.project).render);
  if (files.length === 0) throw new Error("No chapters resolved from _quarto.yml");
  return files;
}

function authorFiles(data: Json): string[] {
  const files = chapterFiles(configFrom(data));
  const information = object(data.fileInformation);
  return files.map((file) => {
    if (!/^index\.(?:md|qmd)$/.test(file)) return file;
    const includeMap = object(information[file]).includeMap;
    if (!Array.isArray(includeMap) || includeMap.length !== 1) return file;
    const target = object(includeMap[0]).target;
    return typeof target === "string" && target !== "" ? target : file;
  });
}

function scalar(value: unknown, fallback = ""): string {
  if (typeof value === "string" || typeof value === "number") return String(value);
  if (Array.isArray(value)) {
    return value.map((item) => scalar(item)).filter(Boolean).join("; ");
  }
  if (value && typeof value === "object") {
    const record = value as Json;
    if (record.name) return scalar(record.name);
  }
  return fallback;
}

function outputFile(config: Json): string {
  return scalar(object(config.book)["output-file"], "longform-document");
}

function outputDir(config: Json): string {
  return scalar(object(config.project)["output-dir"], "build");
}

function gfmTocDepth(config: Json): string {
  const depth = scalar(
    object(config.longform)["gfm-toc-depth"],
    scalar(config["toc-depth"], "2"),
  );
  if (!/^[1-9][0-9]*$/.test(depth)) {
    throw new Error("longform.gfm-toc-depth must be a positive integer");
  }
  return depth;
}

function requiredFonts(config: Json): string[] {
  const value = object(config.longform)["required-fonts"];
  if (value === undefined) return [];
  if (!Array.isArray(value)) {
    throw new Error("longform.required-fonts must be a list of font family names");
  }
  const fonts = value.map((font) => typeof font === "string" ? font.trim() : "");
  if (fonts.some((font) => font === "")) {
    throw new Error("longform.required-fonts must contain only non-empty strings");
  }
  return fonts;
}

function zettlrProject(data: Json) {
  const config = configFrom(data);
  return {
    sorting: "name-up",
    project: {
      title: scalar(object(config.book).title, "Longform document"),
      profiles: [],
      files: authorFiles(data),
      cslStyle: scalar(config.csl),
      templates: { tex: "", html: "" },
    },
    icon: null,
    color: null,
  };
}

async function syncHomeAdapter(checkOnly: boolean) {
  let current = "";
  try {
    current = await Deno.readTextFile(homeAdapterPath);
  } catch (error) {
    if (!(error instanceof Deno.errors.NotFound)) throw error;
  }
  if (checkOnly) {
    if (current !== homeAdapter) {
      throw new Error("index.md is stale; run bin/longform setup");
    }
    return;
  }
  if (current !== homeAdapter) {
    await Deno.writeTextFile(homeAdapterPath, homeAdapter);
    console.log(`Wrote ${relative(projectDir, homeAdapterPath)}`);
  }
}

async function sync(checkOnly: boolean) {
  await syncHomeAdapter(checkOnly);
  const data = await inspect();
  const path = join(projectDir, ".ztr-directory");
  const expected = `${JSON.stringify(zettlrProject(data), null, 2)}\n`;
  let current = "";
  try {
    current = await Deno.readTextFile(path);
  } catch (error) {
    if (!(error instanceof Deno.errors.NotFound)) throw error;
  }
  if (checkOnly) {
    if (current !== expected) {
      throw new Error(".ztr-directory is stale; run bin/longform zettlr sync");
    }
    return;
  }
  await Deno.writeTextFile(path, expected);
  console.log(`Wrote ${relative(projectDir, path)}`);
}

function bibliographyPaths(config: Json): string[] {
  const value = config.bibliography;
  if (typeof value === "string") return [value];
  return strings(value);
}

async function citationIds(files: string[]): Promise<Set<string>> {
  const output = await run(quarto, [
    "pandoc",
    ...files,
    "--from=markdown",
    "--to=json",
  ]);
  const ast = JSON.parse(output);
  const ids = new Set<string>();
  const visit = (value: unknown) => {
    if (Array.isArray(value)) {
      value.forEach(visit);
    } else if (value && typeof value === "object") {
      const record = value as Json;
      if (record.t === "Cite" && Array.isArray(record.c)) {
        const citations = record.c[0];
        if (Array.isArray(citations)) {
          for (const citation of citations) {
            const id = object(citation).citationId;
            if (typeof id === "string") ids.add(id);
          }
        }
      }
      Object.values(record).forEach(visit);
    }
  };
  visit(ast);
  return ids;
}

async function checkBibliography(config: Json, files: string[]) {
  const paths = bibliographyPaths(config);
  if (paths.length !== 1) {
    throw new Error("Longform Kit requires exactly one project bibliography");
  }
  const bibliographyPath = join(projectDir, paths[0]);
  const bibliography = JSON.parse(await Deno.readTextFile(bibliographyPath));
  if (!Array.isArray(bibliography)) {
    throw new Error("Bibliography must be a CSL JSON array");
  }

  const available = new Set<string>();
  const duplicates = new Set<string>();
  for (const entry of bibliography) {
    const id = object(entry).id;
    if (typeof id !== "string" || id === "") {
      throw new Error("Every bibliography item needs an id");
    }
    if (available.has(id)) duplicates.add(id);
    available.add(id);
  }
  if (duplicates.size) {
    throw new Error(
      `Duplicate bibliography keys: ${[...duplicates].sort().join(", ")}`,
    );
  }

  const cited = await citationIds(files);
  const missing = [...cited].filter((id) => !available.has(id)).sort();
  if (missing.length) {
    throw new Error(`Missing citation keys: ${missing.join(", ")}`);
  }
  console.log(
    `Citations: ${cited.size} used, ${available.size} available, 0 missing`,
  );
}

async function checkAuthorDirectory() {
  const authorDir = join(projectDir, "document");
  const visit = async (directory: string) => {
    for await (const entry of Deno.readDir(directory)) {
      const path = join(directory, entry.name);
      if (entry.isDirectory) {
        await visit(path);
      } else if (
        entry.isFile &&
        directory === authorDir &&
        manuscriptMetadataFiles.has(entry.name)
      ) {
        // Manuscript metadata is author-owned information about the document,
        // so it may sit beside the prose even though it is YAML, not Markdown.
      } else if (!entry.isFile || !entry.name.endsWith(".md")) {
        throw new Error(
          `Only author Markdown and ${manuscriptMetadataList} are allowed under document/: ${relative(authorDir, path)}`,
        );
      }
    }
  };
  await visit(authorDir);
}

async function check() {
  await syncHomeAdapter(true);
  const data = await inspect();
  const config = configFrom(data);
  const files = authorFiles(data);
  await checkAuthorDirectory();
  if (files.some((file) => !file.startsWith("document/") || !file.endsWith(".md"))) {
    throw new Error("Every author source must be a Markdown file under document/");
  }
  for (const file of files) await Deno.stat(join(projectDir, file));

  const csl = scalar(config.csl);
  if (!csl) throw new Error("_quarto.yml must declare a project-local CSL file");
  await Deno.stat(join(projectDir, csl));
  await sync(true);
  await checkBibliography(config, files);
  gfmTocDepth(config);
  requiredFonts(config);
  console.log(`Project: ${files.length} ordered source files, configuration valid`);
}

function resolvedDate(book: Json): string {
  const value = scalar(book.date);
  if (value !== "today") return value;
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

function yamlLine(key: string, value: unknown): string {
  return `${key}: ${JSON.stringify(value)}`;
}

function standaloneMetadata(config: Json): string {
  const book = object(config.book);
  const lines = ["---"];
  for (const key of ["title", "subtitle", "author", "date-format"]) {
    const value = book[key];
    if (value !== undefined && value !== "") lines.push(yamlLine(key, value));
  }
  const date = resolvedDate(book);
  if (date) lines.push(yamlLine("date", date));
  lines.push(yamlLine("bibliography", join(projectDir, bibliographyPaths(config)[0])));
  lines.push(yamlLine("csl", join(projectDir, scalar(config.csl))));
  if (config.lang !== undefined) lines.push(yamlLine("lang", config.lang));
  if (config["reference-section-title"] !== undefined) {
    lines.push(
      yamlLine("reference-section-title", config["reference-section-title"]),
    );
  }
  lines.push("toc: true");
  lines.push(`toc-depth: ${gfmTocDepth(config)}`);
  lines.push(`number-sections: ${config["number-sections"] === true}`);
  lines.push(`link-citations: ${config["link-citations"] === true}`);
  lines.push("---", "");
  return lines.join("\n");
}

async function copyDirectory(source: string, destination: string) {
  await Deno.mkdir(destination, { recursive: true });
  for await (const entry of Deno.readDir(source)) {
    const from = join(source, entry.name);
    const to = join(destination, entry.name);
    if (entry.isDirectory) await copyDirectory(from, to);
    else if (entry.isFile) await Deno.copyFile(from, to);
    else throw new Error(`Unsupported vendored extension entry: ${from}`);
  }
}

async function mirrorProjectResources(destination: string) {
  const excluded = new Set(["_extensions", "build", "index.md", "_quarto.yml"]);
  for await (const entry of Deno.readDir(projectDir)) {
    if (
      entry.name.startsWith(".") ||
      entry.name.startsWith("_quarto-") ||
      entry.name.endsWith("_files") ||
      excluded.has(entry.name)
    ) {
      continue;
    }
    await Deno.symlink(
      join(projectDir, entry.name),
      join(destination, entry.name),
    );
  }
}

async function removeIfPresent(path: string) {
  try {
    await Deno.remove(path, { recursive: true });
  } catch (error) {
    if (!(error instanceof Deno.errors.NotFound)) throw error;
  }
}

async function buildGfm() {
  const data = await inspect();
  const config = configFrom(data);
  const files = authorFiles(data);
  const temporary = await Deno.makeTempDir({ prefix: "longform-gfm-" });
  try {
    const extensionSource = join(
      projectDir,
      "_extensions",
      "epigraph",
    );
    const extensionDestination = join(
      temporary,
      "_extensions",
      "epigraph",
    );
    await copyDirectory(extensionSource, extensionDestination);
    await mirrorProjectResources(temporary);

    const body = (
      await Promise.all(
        files.map((file) => Deno.readTextFile(join(projectDir, file))),
      )
    ).map((source) => source.trim()).join("\n\n");
    const source = join(temporary, "longform-gfm.md");
    const temporaryOutput = `${outputFile(config)}.md`;
    const mediaDirectory = `${outputFile(config)}_files`;
    await Deno.writeTextFile(
      source,
      `${standaloneMetadata(config)}${body}\n`,
    );
    await run(
      quarto,
      [
        "render",
        "longform-gfm.md",
        "--to",
        "gfm",
        "--output",
        temporaryOutput,
        `--extract-media=${mediaDirectory}`,
      ],
      { cwd: temporary, stdout: "inherit", stderr: "inherit" },
    );

    const directory = join(projectDir, outputDir(config));
    const output = join(directory, temporaryOutput);
    const stagedMedia = join(temporary, mediaDirectory);
    const outputMedia = join(directory, mediaDirectory);
    await Deno.mkdir(directory, { recursive: true });
    await Deno.copyFile(join(temporary, temporaryOutput), output);
    await removeIfPresent(outputMedia);
    try {
      const media = await Deno.stat(stagedMedia);
      if (media.isDirectory) await copyDirectory(stagedMedia, outputMedia);
    } catch (error) {
      if (!(error instanceof Deno.errors.NotFound)) throw error;
    }
    console.log(`Wrote ${relative(projectDir, output)}`);
  } finally {
    await Deno.remove(temporary, { recursive: true });
  }
}

async function renderLicense(): Promise<string> {
  const config = configFrom(await inspect());
  const author = scalar(object(config.book).author).trim() || "The Author";
  const year = String(new Date().getFullYear());
  const template = await Deno.readTextFile(
    join(projectDir, "share", "templates", "LICENSE.in"),
  );
  return template
    .replaceAll("<YEAR>", year)
    .replaceAll("<AUTHOR>", author)
    .replace(/\n+$/, "\n");
}

const [command, argument] = Deno.args;
try {
  switch (command) {
    case "sync":
      await sync(false);
      break;
    case "check":
      await check();
      break;
    case "gfm":
      await buildGfm();
      break;
    case "license": {
      await Deno.stdout.write(new TextEncoder().encode(await renderLicense()));
      break;
    }
    case "info": {
      const config = configFrom(await inspect());
      if (argument === "output-file") console.log(outputFile(config));
      else if (argument === "output-dir") console.log(outputDir(config));
      else if (argument === "author") {
        console.log(scalar(object(config.book).author).trim());
      } else if (argument === "required-fonts") {
        console.log(requiredFonts(config).join("\n"));
      } else {
        throw new Error(
          "info expects output-file, output-dir, author, or required-fonts",
        );
      }
      break;
    }
    default:
      throw new Error("Expected sync, check, gfm, license, or info");
  }
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  Deno.exit(1);
}
