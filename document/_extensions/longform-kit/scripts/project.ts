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
const extensionDir = dirname(dirname(scriptPath));
const projectDir = dirname(dirname(extensionDir));
const quarto = Deno.env.get("LONGFORM_QUARTO") || "quarto";

async function run(
  command: string,
  args: string[],
  options: { stdout?: "inherit" | "piped"; stderr?: "inherit" | "piped" } = {},
) {
  const result = await new Deno.Command(command, {
    args,
    cwd: projectDir,
    stdout: options.stdout || "piped",
    stderr: options.stderr || "piped",
  }).output();
  if (!result.success) {
    const error = options.stderr === "inherit"
      ? ""
      : new TextDecoder().decode(result.stderr).trim();
    throw new Error(error || `${command} exited with ${result.code}`);
  }
  return options.stdout === "inherit" ? "" : new TextDecoder().decode(result.stdout);
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
  return Array.isArray(value) ? value.filter((item) => typeof item === "string") : [];
}

function configFrom(data: Json): Json {
  return object(data.config);
}

function chapterFiles(config: Json): string[] {
  const project = object(config.project);
  const files = strings(project.render);
  if (files.length === 0) throw new Error("No chapters resolved from _quarto.yml");
  return files;
}

function scalar(value: unknown, fallback = ""): string {
  if (typeof value === "string" || typeof value === "number") return String(value);
  if (Array.isArray(value)) return value.map((item) => scalar(item)).filter(Boolean).join("; ");
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

function zettlrProject(config: Json) {
  return {
    sorting: "name-up",
    project: {
      title: scalar(object(config.book).title, "Longform document"),
      profiles: [],
      files: chapterFiles(config),
      cslStyle: scalar(config.csl),
      templates: { tex: "", html: "" },
    },
    icon: null,
    color: null,
  };
}

async function sync(checkOnly: boolean) {
  const config = configFrom(await inspect());
  const path = join(projectDir, ".ztr-directory");
  const expected = `${JSON.stringify(zettlrProject(config), null, 2)}\n`;
  let current = "";
  try {
    current = await Deno.readTextFile(path);
  } catch (error) {
    if (!(error instanceof Deno.errors.NotFound)) throw error;
  }
  if (checkOnly) {
    if (current !== expected) {
      throw new Error("document/.ztr-directory is stale; run bin/longform zettlr sync");
    }
    return;
  }
  await Deno.writeTextFile(path, expected);
  console.log(`Wrote ${relative(dirname(projectDir), path)}`);
}

function bibliographyPaths(config: Json): string[] {
  const value = config.bibliography;
  if (typeof value === "string") return [value];
  return strings(value);
}

async function citationIds(files: string[]): Promise<Set<string>> {
  const output = await run(quarto, ["pandoc", ...files, "--from=markdown", "--to=json"]);
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
    throw new Error("Longform Kit v1 requires exactly one project bibliography");
  }
  const bibliographyPath = join(projectDir, paths[0]);
  const bibliography = JSON.parse(await Deno.readTextFile(bibliographyPath));
  if (!Array.isArray(bibliography)) throw new Error("Bibliography must be a CSL JSON array");

  const available = new Set<string>();
  const duplicates = new Set<string>();
  for (const entry of bibliography) {
    const id = object(entry).id;
    if (typeof id !== "string" || id === "") throw new Error("Every bibliography item needs an id");
    if (available.has(id)) duplicates.add(id);
    available.add(id);
  }
  if (duplicates.size) throw new Error(`Duplicate bibliography keys: ${[...duplicates].sort().join(", ")}`);

  const cited = await citationIds(files);
  const missing = [...cited].filter((id) => !available.has(id)).sort();
  if (missing.length) throw new Error(`Missing citation keys: ${missing.join(", ")}`);
  console.log(`Citations: ${cited.size} used, ${available.size} available, 0 missing`);
}

async function validateSemantics(files: string[]) {
  await run(quarto, [
    "pandoc",
    ...files,
    "--from=markdown",
    "--to=native",
    "--metadata-file=_quarto.yml",
    `--lua-filter=${join(extensionDir, "pagebreak.lua")}`,
    `--lua-filter=${join(extensionDir, "longform.lua")}`,
  ]);
}

async function check() {
  const data = await inspect();
  const config = configFrom(data);
  const files = chapterFiles(config);
  for (const file of files) await Deno.stat(join(projectDir, file));
  const csl = scalar(config.csl);
  if (!csl) throw new Error("_quarto.yml must declare a project-local CSL file");
  await Deno.stat(join(projectDir, csl));
  await sync(true);
  await checkBibliography(config, files);
  await validateSemantics(files);
  console.log(`Project: ${files.length} ordered source files, configuration valid`);
}

function metadataArgs(config: Json): string[] {
  const book = object(config.book);
  const args = ["--metadata-file=_quarto.yml"];
  for (const key of ["title", "subtitle", "author", "date", "date-format"]) {
    let value = scalar(book[key]);
    if (key === "date" && value === "today") value = new Date().toISOString().slice(0, 10);
    if (value) args.push(`--metadata=${key}:${value}`);
  }
  return args;
}

async function buildGfm() {
  const config = configFrom(await inspect());
  const files = chapterFiles(config);
  const directory = join(projectDir, outputDir(config));
  const output = join(directory, `${outputFile(config)}.md`);
  await Deno.mkdir(directory, { recursive: true });
  await run(quarto, [
    "pandoc",
    ...files,
    "--from=markdown",
    "--to=gfm-raw_html",
    "--standalone",
    "--toc",
    `--toc-depth=${scalar(config["toc-depth"], "2")}`,
    "--top-level-division=chapter",
    "--metadata=link-citations:false",
    ...metadataArgs(config),
    `--template=${join(extensionDir, "gfm.template.md")}`,
    `--lua-filter=${join(extensionDir, "pagebreak.lua")}`,
    `--lua-filter=${join(extensionDir, "longform.lua")}`,
    `--output=${output}`,
  ], { stdout: "inherit", stderr: "inherit" });
  console.log(`Wrote ${relative(dirname(projectDir), output)}`);
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
    case "info": {
      const config = configFrom(await inspect());
      if (argument === "output-file") console.log(outputFile(config));
      else if (argument === "output-dir") console.log(outputDir(config));
      else throw new Error("info expects output-file or output-dir");
      break;
    }
    default:
      throw new Error("Expected sync, check, gfm, or info");
  }
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  Deno.exit(1);
}
