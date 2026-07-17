type Json = Record<string, unknown>;

function dirname(path: string): string {
  const normalized = path.replace(/\\/g, "/").replace(/\/+$/, "");
  const index = normalized.lastIndexOf("/");
  return index <= 0 ? "/" : normalized.slice(0, index);
}

function basename(path: string): string {
  const normalized = path.replace(/\\/g, "/").replace(/\/+$/, "");
  const index = normalized.lastIndexOf("/");
  return index < 0 ? normalized : normalized.slice(index + 1);
}

function join(...parts: string[]): string {
  return parts.join("/").replace(/\\/g, "/").replace(/\/+/g, "/");
}

function isAbsolute(path: string): boolean {
  return path.startsWith("/") || /^[A-Za-z]:[\\/]/.test(path) ||
    path.startsWith("\\\\");
}

function relative(base: string, path: string): string {
  return path.startsWith(`${base}/`) ? path.slice(base.length + 1) : path;
}

function absolute(path: string): string {
  return isAbsolute(path) ? path.replace(/\\/g, "/") : join(projectDir, path);
}

function object(value: unknown): Json {
  return value && typeof value === "object" && !Array.isArray(value)
    ? value as Json
    : {};
}

function strings(value: unknown): string[] {
  if (typeof value === "string") return [value];
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function scalar(value: unknown, fallback = ""): string {
  if (typeof value === "string" || typeof value === "number") {
    return String(value);
  }
  if (Array.isArray(value)) {
    return value.map((item) => scalar(item)).filter(Boolean).join("; ");
  }
  if (value && typeof value === "object") {
    const record = value as Json;
    if (record.name !== undefined) return scalar(record.name, fallback);
  }
  return fallback;
}

const decodedScriptPath = decodeURIComponent(new URL(import.meta.url).pathname);
const scriptPath = Deno.build.os === "windows"
  ? decodedScriptPath.replace(/^\/(?=[A-Za-z]:)/, "")
  : decodedScriptPath;
const projectDir = dirname(dirname(scriptPath));
const quarto = Deno.env.get("QUARTO") || "quarto";
const decoder = new TextDecoder();

async function runQuarto(
  args: string[],
  options: {
    cwd?: string;
    capture?: boolean;
    env?: Record<string, string>;
  } = {},
): Promise<string> {
  const capture = options.capture === true;
  if (capture) {
    const process = new Deno.Command(quarto, {
      args,
      cwd: options.cwd || projectDir,
      env: options.env,
      stdout: "piped",
      stderr: "piped",
    });
    const result = await process.output();
    if (!result.success) {
      const detail = decoder.decode(result.stderr).trim();
      throw new Error(detail || `${quarto} ${args.join(" ")} failed`);
    }
    return decoder.decode(result.stdout);
  }

  // LuaTeX may briefly leave font-cache helpers alive after Quarto exits.
  // Giving renderers inherited or piped descriptors lets those helpers keep a
  // captured CI/build command open indefinitely. Render quietly and report the
  // exact failing command; users can run that Quarto command directly for its
  // full diagnostic stream.
  const child = new Deno.Command(quarto, {
    args,
    cwd: options.cwd || projectDir,
    env: options.env,
    stdout: "null",
    stderr: "null",
  }).spawn();
  const status = await child.status;
  if (!status.success) throw new Error(`${quarto} ${args.join(" ")} failed`);
  return "";
}

async function inspect(profile?: string): Promise<Json> {
  const args = ["inspect"];
  if (profile) args.push("--profile", profile);
  return JSON.parse(await runQuarto(args, { capture: true })) as Json;
}

function configFrom(data: Json): Json {
  return object(data.config);
}

function outputFile(config: Json): string {
  return scalar(object(config.book)["output-file"], "longform-document");
}

function outputDir(config: Json): string {
  return absolute(scalar(object(config.project)["output-dir"], "build"));
}

function chapterFiles(data: Json): string[] {
  const files = strings(object(configFrom(data).project).render);
  if (files.length === 0) {
    throw new Error("Quarto did not resolve any manuscript chapters");
  }
  return files;
}

// index.md is Quarto's project adapter. The combined GFM and Zettlr project
// should expose the author-owned front matter it includes instead.
function authorFiles(data: Json): string[] {
  const information = object(data.fileInformation);
  return chapterFiles(data).map((file) => {
    if (!/^index\.(?:md|qmd)$/.test(file)) return file;
    const includeMap = object(information[file]).includeMap;
    if (!Array.isArray(includeMap) || includeMap.length !== 1) return file;
    const target = object(includeMap[0]).target;
    return typeof target === "string" && target !== "" ? target : file;
  });
}

async function removeIfPresent(path: string): Promise<void> {
  try {
    await Deno.remove(path, { recursive: true });
  } catch (error) {
    if (!(error instanceof Deno.errors.NotFound)) throw error;
  }
}

async function copyDirectory(source: string, destination: string) {
  await Deno.mkdir(destination, { recursive: true });
  for await (const entry of Deno.readDir(source)) {
    const from = join(source, entry.name);
    const to = join(destination, entry.name);
    if (entry.isDirectory) await copyDirectory(from, to);
    else if (entry.isFile) await Deno.copyFile(from, to);
    else throw new Error(`Unsupported generated media entry: ${from}`);
  }
}

async function findFile(directory: string, filename: string): Promise<string> {
  for await (const entry of Deno.readDir(directory)) {
    const path = join(directory, entry.name);
    if (entry.isFile && entry.name === filename) return path;
    if (entry.isDirectory) {
      try {
        return await findFile(path, filename);
      } catch (error) {
        if (!(error instanceof Deno.errors.NotFound)) throw error;
      }
    }
  }
  throw new Deno.errors.NotFound(filename);
}

async function filesWithExtension(
  directory: string,
  extension: string,
): Promise<string[]> {
  const matches: string[] = [];
  for await (const entry of Deno.readDir(directory)) {
    const path = join(directory, entry.name);
    if (entry.isFile && entry.name.endsWith(extension)) matches.push(path);
    else if (entry.isDirectory) {
      matches.push(...await filesWithExtension(path, extension));
    }
  }
  return matches;
}

async function findRenderedFile(
  directory: string,
  filename: string,
): Promise<string> {
  try {
    return await findFile(directory, filename);
  } catch (error) {
    if (!(error instanceof Deno.errors.NotFound)) throw error;
  }

  // Quarto slugifies some book output names (notably names containing spaces)
  // even when `book.output-file` retains the display spelling. Each native
  // format has its own staging directory, so a single file of the requested
  // type is unambiguous and can still be promoted under the configured name.
  const dot = filename.lastIndexOf(".");
  const extension = dot >= 0 ? filename.slice(dot) : "";
  const matches = extension ? await filesWithExtension(directory, extension) : [];
  if (matches.length === 1) return matches[0];
  throw new Deno.errors.NotFound(filename);
}

async function requireOutput(path: string): Promise<void> {
  let information: Deno.FileInfo;
  try {
    information = await Deno.stat(path);
  } catch (error) {
    if (error instanceof Deno.errors.NotFound) {
      throw new Error(`Expected build output was not produced: ${path}`);
    }
    throw error;
  }
  if (!information.isFile || information.size === 0) {
    throw new Error(`Build output is empty or invalid: ${path}`);
  }
}

async function renderNative(
  format: "pdf" | "docx",
  stage: string,
  filename: string,
  profile?: string,
): Promise<string> {
  console.log(`Rendering ${profile === "binding" ? "binding PDF" : format.toUpperCase()}`);
  await Deno.mkdir(stage, { recursive: true });
  const args = ["render"];
  if (profile) args.push("--profile", profile);
  args.push("--to", format, "--output-dir", stage);
  const env: Record<string, string> = {};
  if (format === "pdf") {
    const cache = join(projectDir, ".cache", "texmf");
    if (!Deno.env.get("TEXMFCACHE")) env.TEXMFCACHE = cache;
    if (!Deno.env.get("TEXMFVAR")) env.TEXMFVAR = cache;
    if (Object.keys(env).length > 0) await Deno.mkdir(cache, { recursive: true });
  }
  await runQuarto(args, { env });
  let output: string;
  try {
    output = await findRenderedFile(stage, filename);
  } catch (error) {
    if (error instanceof Deno.errors.NotFound) {
      throw new Error(`Quarto did not produce ${filename}`);
    }
    throw error;
  }
  await requireOutput(output);
  return output;
}

function standaloneMetadata(config: Json): string {
  const book = object(config.book);
  const lines = ["---"];
  for (const key of ["title", "subtitle", "author", "date", "date-format"]) {
    const value = book[key];
    if (value !== undefined && value !== "") {
      lines.push(`${key}: ${JSON.stringify(value)}`);
    }
  }
  if (config.lang !== undefined && config.lang !== "") {
    lines.push(`lang: ${JSON.stringify(config.lang)}`);
  }
  lines.push("---", "");
  return lines.join("\n");
}

function resourcePath(config: Json): string {
  const paths = [projectDir];
  for (const configured of strings(config["resource-path"])) {
    const path = absolute(configured);
    if (!paths.includes(path)) paths.push(path);
  }
  const csl = scalar(config.csl);
  if (csl) {
    const directory = dirname(absolute(csl));
    if (!paths.includes(directory)) paths.push(directory);
  }
  return paths.join(Deno.build.os === "windows" ? ";" : ":");
}

type GfmOutput = { markdown: string; media?: string };

async function renderGfm(
  data: Json,
  stage: string,
  filename: string,
): Promise<GfmOutput> {
  console.log("Rendering combined GFM");
  const config = configFrom(data);
  const token = crypto.randomUUID();
  const profile = `longform-gfm-${token}`;
  const sourceName = `longform-gfm-${token}.md`;
  const sourcePath = join(projectDir, sourceName);
  const profilePath = join(projectDir, `_quarto-${profile}.yml`);
  const working = await Deno.makeTempDir({
    dir: projectDir,
    prefix: ".longform-gfm-",
  });
  const mediaName = `${filename.slice(0, -3)}_files`;
  const extractionName = `.longform-media-${token}`;

  try {
    const body = (await Promise.all(
      authorFiles(data).map((file) => Deno.readTextFile(absolute(file))),
    )).map((source) => source.trim()).join("\n\n");
    await Deno.writeTextFile(
      sourcePath,
      `${standaloneMetadata(config)}${body}\n`,
    );
    await Deno.writeTextFile(profilePath, "project:\n  type: default\n");
    await Deno.mkdir(stage, { recursive: true });
    await runQuarto(
      [
        "render",
        sourcePath,
        "--profile",
        profile,
        "--to",
        "gfm",
        "--output",
        filename,
        "--output-dir",
        stage,
        `--extract-media=${extractionName}`,
        `--resource-path=${resourcePath(config)}`,
      ],
      { cwd: working },
    );

    const markdown = await findFile(stage, filename);
    await requireOutput(markdown);
    const rendered = await Deno.readTextFile(markdown);
    if (rendered.includes(extractionName)) {
      await Deno.writeTextFile(
        markdown,
        rendered.replaceAll(extractionName, mediaName),
      );
    }
    const candidates = [
      join(projectDir, extractionName),
      join(working, extractionName),
      join(stage, extractionName),
    ];
    for (const candidate of candidates) {
      try {
        const information = await Deno.stat(candidate);
        if (information.isDirectory) {
          const staged = join(stage, `.staged-${mediaName}`);
          if (candidate !== staged) await copyDirectory(candidate, staged);
          return { markdown, media: staged };
        }
      } catch (error) {
        if (!(error instanceof Deno.errors.NotFound)) throw error;
      }
    }
    return { markdown };
  } finally {
    await removeIfPresent(sourcePath);
    await removeIfPresent(profilePath);
    await removeIfPresent(join(projectDir, extractionName));
    await removeIfPresent(working);
  }
}

async function promoteFile(source: string, destination: string) {
  await requireOutput(source);
  await Deno.copyFile(source, destination);
  console.log(`Wrote ${relative(projectDir, destination)}`);
}

async function build(): Promise<void> {
  const data = await inspect();
  const bindingData = await inspect("binding");
  const config = configFrom(data);
  const destination = outputDir(config);
  const base = outputFile(config);
  const bindingBase = outputFile(configFrom(bindingData));
  const stage = await Deno.makeTempDir({ prefix: "longform-build-" });

  try {
    const pdf = await renderNative(
      "pdf",
      join(stage, "pdf"),
      `${base}.pdf`,
    );
    const binding = await renderNative(
      "pdf",
      join(stage, "binding"),
      `${bindingBase}.pdf`,
      "binding",
    );
    const docx = await renderNative(
      "docx",
      join(stage, "docx"),
      `${base}.docx`,
    );
    const gfm = await renderGfm(
      data,
      join(stage, "gfm"),
      `${base}.md`,
    );

    await Deno.mkdir(destination, { recursive: true });
    await promoteFile(pdf, join(destination, `${base}.pdf`));
    await promoteFile(binding, join(destination, `${bindingBase}.pdf`));
    await promoteFile(docx, join(destination, `${base}.docx`));
    await promoteFile(gfm.markdown, join(destination, `${base}.md`));

    const mediaDestination = join(destination, `${base}_files`);
    await removeIfPresent(mediaDestination);
    if (gfm.media) await copyDirectory(gfm.media, mediaDestination);

    // Remove products from the retired LaTeX export without touching any
    // author-owned files or unrelated build outputs.
    await removeIfPresent(join(destination, `${base}.tex`));
    await removeIfPresent(join(destination, `${base}-latex`));
  } finally {
    await removeIfPresent(stage);
  }
  console.log("Build complete");
}

function documentRelative(path: string): string {
  if (isAbsolute(path)) return path;
  return path.startsWith("document/")
    ? path.slice("document/".length)
    : `../${path}`;
}

async function zettlr(): Promise<void> {
  const data = await inspect();
  const config = configFrom(data);
  const csl = scalar(config.csl);
  const adapter = {
    sorting: "name-up",
    project: {
      title: scalar(object(config.book).title, "Longform document"),
      profiles: [],
      files: authorFiles(data).map(documentRelative),
      cslStyle: csl ? documentRelative(csl) : "",
      templates: { tex: "", html: "" },
    },
    icon: null,
    color: null,
  };
  const destination = join(projectDir, "document", ".ztr-directory");
  await Deno.writeTextFile(destination, `${JSON.stringify(adapter, null, 2)}\n`);
  console.log(`Wrote ${relative(projectDir, destination)}`);
}

function usage(): string {
  return [
    "Usage: quarto run scripts/longform.ts build|zettlr",
    "",
    "  build   Render one-sided PDF, binding PDF, DOCX, and combined GFM",
    "  zettlr  Synchronize document/.ztr-directory with Quarto chapter order",
  ].join("\n");
}

const [command, ...arguments_] = Deno.args;
try {
  if (arguments_.length !== 0) throw new Error(usage());
  if (command === "build") await build();
  else if (command === "zettlr") await zettlr();
  else throw new Error(usage());
  // `quarto run` can otherwise keep inherited renderer handles alive when its
  // output is captured by a test runner or CI process.
  Deno.exit(0);
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  Deno.exit(1);
}
