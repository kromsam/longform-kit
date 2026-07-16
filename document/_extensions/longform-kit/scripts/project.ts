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

function gfmSource(config: Json): "markdown" | "latex" {
  const configured = object(config.longform)["gfm-source"];
  const source = configured === undefined ? "markdown" : configured;
  if (source !== "markdown" && source !== "latex") {
    throw new Error("longform.gfm-source must be markdown or latex");
  }
  return source;
}

function validateGfmConfig(config: Json): "markdown" | "latex" {
  const source = gfmSource(config);
  gfmTocDepth(config);
  gfmLegacyPlainScalars(config);
  if (source === "latex" && config["link-citations"] !== false) {
    throw new Error(
      "longform.gfm-source: latex requires link-citations: false so citation text survives the LaTeX round trip",
    );
  }
  return source;
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

function gfmLegacyPlainScalars(config: Json): boolean {
  const value = object(config.longform)["gfm-legacy-plain-scalars"];
  if (value === undefined) return false;
  if (typeof value !== "boolean") {
    throw new Error("longform.gfm-legacy-plain-scalars must be true or false");
  }
  return value;
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
  validateGfmConfig(config);
  requiredFonts(config);
  console.log(`Project: ${files.length} ordered source files, configuration valid`);
}

function metadataArgs(config: Json): string[] {
  const book = object(config.book);
  const args = ["--metadata-file=_quarto.yml"];
  for (const key of ["title", "subtitle", "author", "date", "date-format"]) {
    const value = key === "date" ? resolvedDate(book) : scalar(book[key]);
    if (value) args.push(`--metadata=${key}:${value}`);
  }
  return args;
}

function resolvedDate(book: Json): string {
  const value = scalar(book.date);
  if (value !== "today") return value;
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

function yamlScalar(
  value: string,
  alwaysQuote = false,
  preserveImplicit = false,
): string {
  const implicit = /^(?:~|null|true|false|yes|no|on|off|\.nan|[+-]?\.inf)$/i.test(value) ||
    /^[+-]?(?:[0-9][0-9_]*(?:\.[0-9_]*)?|\.[0-9_]+)(?:e[+-]?[0-9]+)?$/i.test(value) ||
    /^[+-]?0[xob][0-9a-f_]+$/i.test(value) ||
    /^[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}(?:$|[Tt ])/.test(value);
  const unsafe = alwaysQuote || /[\r\n:#]/.test(value) ||
    /^\s|\s$|^[\-?:,\[\]{}&*!|>'"%@`]/.test(value) ||
    (!preserveImplicit && implicit);
  return unsafe ? JSON.stringify(value) : value;
}

function authorValues(book: Json): string[] {
  const value = book.author;
  if (Array.isArray(value)) {
    return value.map((author) => scalar(author)).filter(Boolean);
  }
  const author = scalar(value);
  return author ? [author] : [];
}

function gfmVariableArgs(config: Json): string[] {
  const book = object(config.book);
  const longform = object(config.longform);
  const preserveImplicit = gfmLegacyPlainScalars(config);
  const values: Array<[string, string, boolean?]> = [
    ["date-yaml", resolvedDate(book)],
    ["degreetitle-yaml", scalar(longform["degree-title"])],
    ["institute-yaml", scalar(longform.institute)],
    ["lang-yaml", scalar(config.lang, "en-GB")],
    ["reference-section-title-yaml", scalar(config["reference-section-title"], "Bibliography")],
    ["studentnumber-yaml", scalar(longform["student-number"])],
    ["subtitle-yaml", scalar(book.subtitle), true],
    ["supervisor-yaml", scalar(longform.supervisor)],
    ["title-yaml", scalar(book.title)],
  ];
  const args = values
    .filter(([, value]) => value !== "")
    .map(([key, value, alwaysQuote]) =>
      `--variable=${key}:${yamlScalar(value, alwaysQuote, preserveImplicit)}`
    );
  for (const author of authorValues(book)) {
    args.push(`--variable=author-yaml:${yamlScalar(author, false, preserveImplicit)}`);
  }
  return args;
}

async function buildMarkdownGfm(config: Json) {
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
    `--toc-depth=${gfmTocDepth(config)}`,
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

async function buildLatexGfm(config: Json) {
  validateGfmConfig(config);
  const directory = join(projectDir, outputDir(config));
  const latex = join(directory, `${outputFile(config)}.tex`);
  const output = join(directory, `${outputFile(config)}.md`);
  try {
    await Deno.stat(latex);
  } catch (error) {
    if (error instanceof Deno.errors.NotFound) {
      throw new Error("GFM export requires the canonical LaTeX build first");
    }
    throw error;
  }
  await Deno.mkdir(directory, { recursive: true });
  await run(quarto, [
    "pandoc",
    latex,
    "--from=latex",
    "--to=gfm+raw_html",
    "--standalone",
    "--toc",
    `--toc-depth=${gfmTocDepth(config)}`,
    ...metadataArgs(config),
    ...gfmVariableArgs(config),
    `--template=${join(extensionDir, "gfm-latex.template.md")}`,
    `--output=${output}`,
  ], { stdout: "inherit", stderr: "inherit" });
  console.log(`Wrote ${relative(dirname(projectDir), output)}`);
}

async function buildGfm() {
  const config = configFrom(await inspect());
  if (gfmSource(config) === "latex") await buildLatexGfm(config);
  else await buildMarkdownGfm(config);
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
      else if (argument === "gfm-source") console.log(gfmSource(config));
      else if (argument === "required-fonts") {
        console.log(requiredFonts(config).join("\n"));
      } else {
        throw new Error("info expects output-file, output-dir, gfm-source, or required-fonts");
      }
      break;
    }
    default:
      throw new Error("Expected sync, check, gfm, or info");
  }
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  Deno.exit(1);
}
