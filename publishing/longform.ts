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

function profilesWith(data: Json, temporary: string): string {
  const active = strings(object(data.files).config)
    .map(basename)
    .filter((file) => file.startsWith("_quarto-") && file.endsWith(".yml"))
    .map((file) => file.slice("_quarto-".length, -".yml".length));
  return [temporary, ...active.filter((profile) => profile !== temporary)]
    .join(",");
}

const decodedScriptPath = decodeURIComponent(new URL(import.meta.url).pathname);
const scriptPath = Deno.build.os === "windows"
  ? decodedScriptPath.replace(/^\/(?=[A-Za-z]:)/, "")
  : decodedScriptPath;
const projectDir = dirname(dirname(scriptPath));
const quarto = Deno.env.get("QUARTO") || "quarto";
const pdfjam = Deno.env.get("PDFJAM") || "pdfjam";
const qpdf = Deno.env.get("QPDF") || "qpdf";
const lualatex = Deno.env.get("LUALATEX") || "lualatex";
const decoder = new TextDecoder();

type CommandOptions = {
  cwd?: string;
  env?: Record<string, string>;
};

async function runCommand(
  executable: string,
  args: string[],
  label: string,
  options: CommandOptions = {},
): Promise<string> {
  let result: Deno.CommandOutput;
  try {
    result = await new Deno.Command(executable, {
      args,
      cwd: options.cwd || projectDir,
      env: options.env,
      stdout: "piped",
      stderr: "piped",
    }).output();
  } catch (error) {
    if (error instanceof Deno.errors.NotFound) {
      throw new Error(`${executable} is required to ${label}`);
    }
    throw error;
  }
  const stdout = decoder.decode(result.stdout);
  const stderr = decoder.decode(result.stderr);
  if (!result.success) {
    const detail = [stderr.trim(), stdout.trim()].filter(Boolean).join("\n");
    throw new Error(detail || `${executable} failed to ${label}`);
  }
  return stdout;
}

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

async function inspect(): Promise<Json> {
  const args = ["inspect"];
  return JSON.parse(await runQuarto(args, { capture: true })) as Json;
}

function configFrom(data: Json): Json {
  return object(data.config);
}

function outputFile(config: Json): string {
  return scalar(object(config.book)["output-file"], "longform-document");
}

function outputDir(config: Json): string {
  return absolute(scalar(object(config.project)["output-dir"], "output"));
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
  const matches = extension
    ? await filesWithExtension(directory, extension)
    : [];
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
): Promise<string> {
  console.log(`Rendering ${format.toUpperCase()}`);
  await Deno.mkdir(stage, { recursive: true });
  const args = ["render"];
  args.push("--to", format, "--output-dir", stage);
  const env: Record<string, string> = {};
  if (format === "pdf") {
    const cache = join(projectDir, ".cache", "texmf");
    if (!Deno.env.get("TEXMFCACHE")) env.TEXMFCACHE = cache;
    if (!Deno.env.get("TEXMFVAR")) env.TEXMFVAR = cache;
    if (Object.keys(env).length > 0) {
      await Deno.mkdir(cache, { recursive: true });
    }
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

function veraPdfProfiles(config: Json): string[] {
  const pdf = object(object(config.format).pdf);
  const standards = strings(pdf["pdf-standard"]);
  const profiles: string[] = [];
  for (const standard of standards) {
    const normalized = standard.trim().toLowerCase();
    const archival = /^a-(1a|1b|2a|2b|2u|3a|3b|3u|4|4e|4f)$/.exec(
      normalized,
    );
    if (archival) profiles.push(archival[1]);
    const accessible = /^ua-([12])$/.exec(normalized);
    if (accessible) profiles.push(`ua${accessible[1]}`);
  }
  return [...new Set(profiles)];
}

async function validatePdfStandards(
  path: string,
  profiles: string[],
): Promise<void> {
  if (Deno.env.get("LONGFORM_VALIDATE_PDF") !== "1") return;
  if (profiles.length === 0) {
    throw new Error(
      "LONGFORM_VALIDATE_PDF=1 requires a configured PDF/A or PDF/UA standard",
    );
  }

  const verifier = Deno.env.get("QUARTO_VERAPDF") || "verapdf";
  for (const profile of profiles) {
    console.log(`Validating PDF with veraPDF profile ${profile}`);
    const output = await runCommand(
      verifier,
      ["-f", profile, path],
      `validate PDF profile ${profile}`,
    );
    const results = [...output.matchAll(/isCompliant=["'](true|false)["']/g)]
      .map((match) => match[1] === "true");
    if (results.length === 0) {
      throw new Error(
        `veraPDF profile ${profile} returned no isCompliant result`,
      );
    }
    if (results.some((result) => !result)) {
      throw new Error(`veraPDF validation failed for profile ${profile}`);
    }
  }
}

type PdfOutline = {
  title: string;
  sourcePage: number;
  level: number;
};

function collectPdfOutlines(
  value: unknown,
  level = 0,
  outlines: PdfOutline[] = [],
): PdfOutline[] {
  if (!Array.isArray(value)) return outlines;
  for (const item of value) {
    const entry = object(item);
    const title = scalar(entry.title).trim();
    const sourcePage = entry.destpageposfrom1;
    if (
      title && typeof sourcePage === "number" && Number.isInteger(sourcePage) &&
      sourcePage > 0
    ) {
      outlines.push({ title, sourcePage, level });
    }
    collectPdfOutlines(entry.kids, level + 1, outlines);
  }
  return outlines;
}

async function readPdfOutlines(path: string): Promise<PdfOutline[]> {
  const version = await runCommand(
    qpdf,
    ["--version"],
    "check qpdf outline support",
  );
  const match = /\bqpdf version (\d+)\.(\d+)(?:\.\d+)?\b/.exec(version);
  if (
    !match || Number(match[1]) < 11 ||
    (Number(match[1]) === 11 && Number(match[2]) < 10)
  ) {
    throw new Error(
      `${qpdf} 11.10 or newer is required to read PDF bookmarks reliably`,
    );
  }
  const output = await runCommand(
    qpdf,
    ["--json", "--json-key=outlines", path],
    "read source PDF bookmarks",
  );
  let payload: Json;
  try {
    payload = JSON.parse(output) as Json;
  } catch {
    throw new Error(
      `${qpdf} returned invalid JSON while reading PDF bookmarks`,
    );
  }
  return collectPdfOutlines(payload.outlines);
}

function plainMetadataText(value: unknown): string {
  let result = scalar(value).trim();
  if (
    result.length >= 2 &&
    ((result.startsWith("*") && result.endsWith("*")) ||
      (result.startsWith("_") && result.endsWith("_")))
  ) {
    result = result.slice(1, -1);
  }
  return result
    .replace(/`([^`]*)`/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/__([^_]+)__/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/_([^_\s](?:.*?[^_\s])?)_/g, "$1")
    .replace(/\\([\\`*_[\]{}()#+.!-])/g, "$1")
    .replace(/\s+/g, " ")
    .trim();
}

function texEscape(value: string): string {
  const replacements: Record<string, string> = {
    "\\": "\\textbackslash{}",
    "{": "\\{",
    "}": "\\}",
    "$": "\\$",
    "&": "\\&",
    "#": "\\#",
    "%": "\\%",
    "_": "\\_",
    "^": "\\textasciicircum{}",
    "~": "\\textasciitilde{}",
  };
  return value
    .replace(/[\u0000-\u001f\u007f]+/g, " ")
    .replace(/[\\{}$&#%_^~]/g, (character) => replacements[character])
    .replace(/\s+/g, " ")
    .trim();
}

type PublicationMetadata = {
  title: string;
  author: string;
  subject: string;
  keywords: string;
  lang: string;
};

function publicationMetadata(config: Json): PublicationMetadata {
  const book = object(config.book);
  const title = plainMetadataText(config["title-meta"]) ||
    [plainMetadataText(book.title), plainMetadataText(book.subtitle)]
      .filter(Boolean).join(": ");
  return {
    title,
    author: plainMetadataText(config["author-meta"] || book.author),
    subject: plainMetadataText(config.subject),
    keywords: strings(config.keywords).map(plainMetadataText).filter(Boolean)
      .join(", ") || plainMetadataText(config.keywords),
    lang: plainMetadataText(config.lang),
  };
}

function twoUpTex(
  metadata: PublicationMetadata,
  outlines: PdfOutline[],
): string {
  const bySheet = new Map<number, PdfOutline[]>();
  for (const outline of outlines) {
    const sheet = Math.floor(outline.sourcePage / 2) + 1;
    const entries = bySheet.get(sheet) || [];
    entries.push(outline);
    bySheet.set(sheet, entries);
  }
  const bookmarkDefinitions = [...bySheet.entries()].map(([sheet, entries]) => {
    const commands = entries.map((entry, index) =>
      `\\pdfbookmark[${entry.level}]{${texEscape(entry.title)}}` +
      `{longform-outline-${sheet}-${index}}`
    ).join("%\n");
    return `\\expandafter\\def\\csname LongformBookmarks${sheet}` +
      `\\endcsname{%\n${commands}%\n}`;
  }).join("\n");
  const settings = [
    `pdftitle={${texEscape(metadata.title)}}`,
    `pdfauthor={${texEscape(metadata.author)}}`,
    `pdfsubject={${texEscape(metadata.subject)}}`,
    `pdfkeywords={${texEscape(metadata.keywords)}}`,
    `pdflang={${texEscape(metadata.lang)}}`,
    "pdfdisplaydoctitle=true",
    "bookmarks=true",
    "bookmarksopen=true",
  ].join(",\n  ");
  return String.raw`\documentclass[a4paper,landscape]{article}
\usepackage[margin=0pt]{geometry}
\usepackage{pdfpages}
\usepackage[unicode,hidelinks]{hyperref}
\hypersetup{
  ${settings}
}
\pagestyle{empty}
\newcounter{LongformSheet}
${bookmarkDefinitions}
\newcommand{\LongformSheetCommand}{%
  \thispagestyle{empty}%
  \stepcounter{LongformSheet}%
  \ifcsname LongformBookmarks\arabic{LongformSheet}\endcsname%
    \csname LongformBookmarks\arabic{LongformSheet}\endcsname%
  \fi%
}
\begin{document}
\includepdf[pages=-,fitpaper=true,pagecommand={\LongformSheetCommand}]{imposed.pdf}
\end{document}
`;
}

async function imposeTwoUp(
  source: string,
  destination: string,
  metadata: PublicationMetadata,
): Promise<string> {
  console.log("Imposing PDF two-up");
  await Deno.mkdir(dirname(destination), { recursive: true });
  const outlines = await readPdfOutlines(source);
  const working = await Deno.makeTempDir({ prefix: "longform-two-up-" });
  const imposed = join(working, "imposed.pdf");
  try {
    await runCommand(
      pdfjam,
      [
        "--vanilla",
        "--quiet",
        source,
        "{},1-",
        "--nup",
        "2x1",
        "--landscape",
        "--paper",
        "a4paper",
        "--outfile",
        imposed,
      ],
      "create the two-up PDF",
      { cwd: working },
    );
    await requireOutput(imposed);

    await Deno.writeTextFile(
      join(working, "longform-two-up.tex"),
      twoUpTex(metadata, outlines),
    );
    const latexArgs = [
      "--interaction=batchmode",
      "--halt-on-error",
      "--file-line-error",
      "longform-two-up.tex",
    ];
    const texEnvironment: Record<string, string> = {};
    const texCache = join(projectDir, ".cache", "texmf");
    if (!Deno.env.get("TEXMFCACHE")) texEnvironment.TEXMFCACHE = texCache;
    if (!Deno.env.get("TEXMFVAR")) texEnvironment.TEXMFVAR = texCache;
    if (Object.keys(texEnvironment).length > 0) {
      await Deno.mkdir(texCache, { recursive: true });
    }
    for (let run = 0; run < 2; run += 1) {
      await runCommand(
        lualatex,
        latexArgs,
        `write two-up PDF metadata and bookmarks (run ${run + 1})`,
        { cwd: working, env: texEnvironment },
      );
    }
    const rendered = join(working, "longform-two-up.pdf");
    await requireOutput(rendered);
    await Deno.copyFile(rendered, destination);
  } finally {
    await removeIfPresent(working);
  }
  await requireOutput(destination);
  return destination;
}

async function sanitizeDocx(
  source: string,
  destination: string,
): Promise<string> {
  console.log("Sanitizing DOCX package metadata");
  await Deno.mkdir(dirname(destination), { recursive: true });
  await runQuarto(
    [
      "pandoc",
      "lua",
      join(projectDir, "publishing", "docx", "sanitize.lua"),
      source,
      destination,
    ],
    { capture: true },
  );
  await requireOutput(destination);
  return destination;
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
  const subtitle = plainMetadataText(book.subtitle);
  if (subtitle) {
    lines.push(`longform-gfm-subtitle: ${JSON.stringify(subtitle)}`);
  }
  if (config.lang !== undefined && config.lang !== "") {
    lines.push(`lang: ${JSON.stringify(config.lang)}`);
  }
  lines.push("---", "");
  return lines.join("\n");
}

function gfmDiscoveryMetadata(config: Json): string {
  const book = object(config.book);
  const identity = publicationMetadata(config);
  const keywordList = strings(config.keywords).map(plainMetadataText)
    .filter(Boolean);
  const fields: [string, string | string[]][] = [
    ["title", plainMetadataText(book.title)],
    ["subtitle", plainMetadataText(book.subtitle)],
    ["title-meta", identity.title],
    ["author", identity.author],
    ["date", plainMetadataText(book.date)],
    ["lang", identity.lang],
    ["subject", identity.subject],
    [
      "keywords",
      keywordList.length > 0
        ? keywordList
        : identity.keywords.split(",").map((keyword) => keyword.trim())
          .filter(Boolean),
    ],
  ];
  const lines = ["---"];
  for (const [key, value] of fields) {
    const populated = Array.isArray(value) ? value.length > 0 : value !== "";
    if (populated) {
      // JSON scalars and arrays are valid YAML and keep punctuation, braces,
      // and non-ASCII discovery metadata unambiguous in the combined GFM.
      lines.push(`${key}: ${JSON.stringify(value)}`);
    }
  }
  lines.push("---", "");
  return lines.join("\n");
}

function gfmTemplate(): string {
  return `$if(title)$
# $title$
$if(longform-gfm-subtitle)$

*$longform-gfm-subtitle$*
$endif$
$for(author)$

$author$
$endfor$
$if(date)$

$date$
$endif$

$endif$
$for(header-includes)$
$header-includes$

$endfor$
$for(include-before)$
$include-before$

$endfor$
$if(toc)$
$table-of-contents$

$endif$
$body$
$for(include-after)$

$include-after$
$endfor$
`;
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
  const templatePath = join(working, "longform-gfm.template");
  const mediaName = `${filename.slice(0, -3)}_files`;
  const mediaReference = encodeURIComponent(mediaName);
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
    await Deno.writeTextFile(templatePath, gfmTemplate());
    await Deno.mkdir(stage, { recursive: true });
    await runQuarto(
      [
        "render",
        sourcePath,
        "--profile",
        profilesWith(data, profile),
        "--to",
        "gfm",
        "--output",
        filename,
        "--output-dir",
        stage,
        `--template=${templatePath}`,
        `--extract-media=${extractionName}`,
        `--resource-path=${resourcePath(config)}`,
      ],
      { cwd: working },
    );

    const markdown = await findFile(stage, filename);
    await requireOutput(markdown);
    const rendered = await Deno.readTextFile(markdown);
    await Deno.writeTextFile(
      markdown,
      `${gfmDiscoveryMetadata(config)}${
        rendered.replaceAll(extractionName, mediaReference)
      }`,
    );
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
  const config = configFrom(data);
  const destination = outputDir(config);
  const base = outputFile(config);
  const twoUpBase = `${base}-2up`;
  const stage = await Deno.makeTempDir({ prefix: "longform-build-" });

  try {
    const pdf = await renderNative(
      "pdf",
      join(stage, "pdf"),
      `${base}.pdf`,
    );
    await validatePdfStandards(pdf, veraPdfProfiles(config));
    const twoUp = await imposeTwoUp(
      pdf,
      join(stage, "pdf-2up", `${twoUpBase}.pdf`),
      publicationMetadata(config),
    );
    const renderedDocx = await renderNative(
      "docx",
      join(stage, "docx"),
      `${base}.docx`,
    );
    const docx = await sanitizeDocx(
      renderedDocx,
      join(stage, "sanitized-docx", `${base}.docx`),
    );
    const gfm = await renderGfm(
      data,
      join(stage, "gfm"),
      `${base}.md`,
    );

    await Deno.mkdir(destination, { recursive: true });
    await promoteFile(pdf, join(destination, `${base}.pdf`));
    await promoteFile(twoUp, join(destination, `${twoUpBase}.pdf`));
    await promoteFile(docx, join(destination, `${base}.docx`));
    await promoteFile(gfm.markdown, join(destination, `${base}.md`));

    const mediaDestination = join(destination, `${base}_files`);
    await removeIfPresent(mediaDestination);
    if (gfm.media) await copyDirectory(gfm.media, mediaDestination);

    // Remove products from retired exports without touching author-owned files
    // or unrelated build outputs.
    await removeIfPresent(join(destination, `${base}-binding.pdf`));
    await removeIfPresent(join(destination, `${base}-binding-2up.pdf`));
    await removeIfPresent(join(destination, `${base}.tex`));
    await removeIfPresent(join(destination, `${base}-latex`));
  } finally {
    await removeIfPresent(stage);
    // LuaLaTeX's tagging/math support can write this MathML sidecar beside
    // Quarto's root adapter even when the public PDF is staged elsewhere.
    await removeIfPresent(join(projectDir, "index-luamml-mathml.html"));
  }
  console.log("Build complete");
}

function writingRelative(path: string): string {
  if (isAbsolute(path)) return path;
  return path.startsWith("writing/")
    ? path.slice("writing/".length)
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
      files: authorFiles(data).map(writingRelative),
      cslStyle: csl ? writingRelative(csl) : "",
      templates: { tex: "", html: "" },
    },
    icon: null,
    color: null,
  };
  const destination = join(projectDir, "writing", ".ztr-directory");
  await Deno.writeTextFile(
    destination,
    `${JSON.stringify(adapter, null, 2)}\n`,
  );
  console.log(`Wrote ${relative(projectDir, destination)}`);
}

function usage(): string {
  return [
    "Usage: quarto run publishing/longform.ts build|zettlr",
    "",
    "  build   Render PDF, two-up PDF, DOCX, and combined GFM",
    "  zettlr  Synchronize writing/.ztr-directory with Quarto chapter order",
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
