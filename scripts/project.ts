type Json = Record<string, unknown>;

function dirname(path: string): string {
  const normalized = path.replace(/\/+$/, "");
  const index = normalized.lastIndexOf("/");
  return index <= 0 ? "/" : normalized.slice(0, index);
}

function join(...parts: string[]): string {
  return parts.join("/").replace(/\/+/g, "/");
}

function basename(path: string): string {
  const normalized = path.replace(/\/+$/, "");
  const index = normalized.lastIndexOf("/");
  return index < 0 ? normalized : normalized.slice(index + 1);
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
// metadata.yml holds title/author/date/language and chapters.yml the chapter
// list. Together with the generated .ztr-directory Zettlr adapter, these are
// the only non-Markdown files allowed at the top of document/.
const manuscriptMetadataFiles = new Set(["metadata.yml", "chapters.yml"]);
const manuscriptMetadataList = [...manuscriptMetadataFiles].join(", ");
const zettlrAdapterFile = ".ztr-directory";
const referencesDir = join(projectDir, "references");
const bibliographyLink = join(referencesDir, "library.json");
const styleLink = join(referencesDir, "style.csl");
const zoteroStylesLink = join(referencesDir, "zotero-styles");
const cslParentsDir = join(referencesDir, ".csl-parents");
const setupLock = join(projectDir, ".cache", "reference-setup.lock");
const epigraphExtension = "quarto/extensions/epigraph";
const epigraphShortcode = `${epigraphExtension}/epigraph.lua`;
const citationResourcePaths = [
  ".",
  "references/.csl-parents",
  "references/zotero-styles",
  "references/zotero-styles/hidden",
];

type SetupOptions = {
  library?: string;
  zoteroDataDir?: string;
  style?: string;
};

type StyleRecord = {
  filename: string;
  path: string;
  title: string;
  id: string;
  source: string;
};

type LinkSpec = {
  target: string;
  destination: string;
};

function expandHome(path: string): string {
  if (path !== "~" && !path.startsWith("~/")) return path;
  const home = Deno.env.get("HOME");
  if (!home) throw new Error("HOME is not set; use an absolute path");
  return path === "~" ? home : join(home, path.slice(2));
}

function absolute(path: string): string {
  const expanded = expandHome(path.trim());
  return expanded.startsWith("/") ? expanded : join(projectDir, expanded);
}

function decodeXml(value: string): string {
  return value
    .replace(
      /&#x([0-9a-f]+);/gi,
      (_match, digits) => String.fromCodePoint(Number.parseInt(digits, 16)),
    )
    .replace(
      /&#([0-9]+);/g,
      (_match, digits) => String.fromCodePoint(Number.parseInt(digits, 10)),
    )
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&");
}

function searchableXml(source: string): string {
  return source
    .replace(/<!--[\s\S]*?-->/g, "")
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, (_match, content) =>
      content
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;"));
}

function xmlElement(source: string, name: string): string {
  const match = searchableXml(source).match(
    new RegExp(
      `<(?:[A-Za-z_][\\w.-]*:)?${name}(?:\\s[^>]*)?>([\\s\\S]*?)</(?:[A-Za-z_][\\w.-]*:)?${name}\\s*>`,
      "i",
    ),
  );
  return match ? decodeXml(match[1].replace(/<[^>]+>/g, "").trim()) : "";
}

function xmlAttribute(source: string, name: string): string {
  const match = source.match(
    new RegExp(`(?:^|\\s)${name}\\s*=\\s*["']([^"']+)["']`, "i"),
  );
  return match ? decodeXml(match[1]) : "";
}

function independentParent(source: string): string {
  for (
    const match of searchableXml(source).matchAll(
      /<(?:[A-Za-z_][\w.-]*:)?link\b[^>]*>/gi,
    )
  ) {
    if (xmlAttribute(match[0], "rel") === "independent-parent") {
      return xmlAttribute(match[0], "href").trim();
    }
  }
  return "";
}

function normalized(value: string): string {
  return value.trim().toLowerCase();
}

function styleMatches(style: StyleRecord, query: string): boolean {
  const wanted = normalized(query);
  return wanted === normalized(style.filename) ||
    wanted === normalized(style.id) ||
    wanted === normalized(style.title);
}

async function stylesInDirectory(directory: string): Promise<StyleRecord[]> {
  const styles: StyleRecord[] = [];
  for await (const entry of Deno.readDir(directory)) {
    if ((!entry.isFile && !entry.isSymlink) || !entry.name.endsWith(".csl")) {
      continue;
    }
    const path = join(directory, entry.name);
    const source = await Deno.readTextFile(path);
    const title = xmlElement(source, "title");
    const id = xmlElement(source, "id");
    if (title && id) {
      styles.push({ filename: entry.name, path, title, id, source });
    }
  }
  return styles;
}

async function installedStyles(stylesDir: string): Promise<StyleRecord[]> {
  return await stylesInDirectory(stylesDir);
}

async function parentStyle(
  stylesDir: string,
  parentId: string,
): Promise<StyleRecord> {
  const directories = [stylesDir, join(stylesDir, "hidden")];
  const styles: StyleRecord[] = [];
  for (const directory of directories) {
    try {
      styles.push(...await stylesInDirectory(directory));
    } catch (error) {
      if (!(error instanceof Deno.errors.NotFound)) throw error;
    }
  }
  const matches = styles.filter((style) => style.id === parentId);
  if (matches.length === 1) return matches[0];
  if (matches.length > 1) {
    throw new Error(
      `Multiple installed CSL styles declare parent ID: ${parentId}`,
    );
  }
  throw new Error(
    `Dependent CSL style is missing its installed parent: ${parentId}`,
  );
}

function parentAliasFilename(parentId: string): string {
  const value = parentId.trim();
  let uri: URL;
  try {
    uri = new URL(value);
  } catch {
    throw new Error(
      `Dependent CSL style has an invalid parent ID: ${parentId}`,
    );
  }
  const protocol = uri.protocol.toLowerCase();
  const component = uri.pathname.split("/").at(-1) || "";
  if (
    (protocol !== "http:" && protocol !== "https:") || !uri.hostname ||
    uri.username || uri.password || uri.search || uri.hash ||
    uri.pathname.endsWith("/") || value.includes("%") ||
    value.includes("?") || value.includes("#") || value.includes("\\") ||
    !/^[A-Za-z0-9._-]+$/.test(component) ||
    component === "." || component === ".."
  ) {
    throw new Error(
      `Dependent CSL parent cannot be resolved offline; use a canonical HTTP(S) style ID ending in an unescaped filename: ${parentId}`,
    );
  }
  return component.endsWith(".csl") ? component : `${component}.csl`;
}

async function dependentParentLink(
  stylesDir: string,
  styleSource: string,
): Promise<LinkSpec | undefined> {
  const parentId = independentParent(styleSource);
  if (!parentId) return undefined;
  const installedParent = await parentStyle(stylesDir, parentId);
  return {
    target: await requireFile(installedParent.path, "Installed CSL parent"),
    destination: join(cslParentsDir, parentAliasFilename(parentId)),
  };
}

async function validateCslStyle(
  stylePath: string,
  parentLink?: LinkSpec,
) {
  let resourceDirectory: string | undefined;
  try {
    if (parentLink) {
      resourceDirectory = await Deno.makeTempDir({
        prefix: "longform-csl-parent-",
      });
      await Deno.symlink(
        parentLink.target,
        join(resourceDirectory, basename(parentLink.destination)),
      );
    }
    const args = [
      "pandoc",
      "--from=markdown",
      "--to=plain",
      "--citeproc",
      `--csl=${stylePath}`,
    ];
    if (resourceDirectory) {
      args.push(`--resource-path=${resourceDirectory}`);
    }
    await run(quarto, args);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`CSL style failed Pandoc validation: ${message}`);
  } finally {
    if (resourceDirectory) {
      await Deno.remove(resourceDirectory, { recursive: true });
    }
  }
}

async function selectStyle(
  stylesDir: string,
  query: string,
): Promise<StyleRecord> {
  const styles = await installedStyles(stylesDir);
  if (styles.length === 0) {
    throw new Error(`No installed CSL styles found in ${stylesDir}`);
  }
  const matches = styles.filter((style) => styleMatches(style, query));
  if (matches.length === 1) return matches[0];
  if (matches.length > 1) {
    throw new Error(
      `CSL style name is ambiguous: ${
        matches.map((style) => `${style.title} [${style.filename}]`).join("; ")
      }`,
    );
  }
  throw new Error(
    `No installed CSL style matches "${query}"; install it in Zotero's Style Manager`,
  );
}

async function requireFile(path: string, label: string): Promise<string> {
  const candidate = absolute(path);
  let information: Deno.FileInfo;
  try {
    information = await Deno.stat(candidate);
  } catch (error) {
    if (error instanceof Deno.errors.NotFound) {
      throw new Error(`${label} does not exist: ${candidate}`);
    }
    throw error;
  }
  if (!information.isFile) {
    throw new Error(`${label} is not a file: ${candidate}`);
  }
  return await Deno.realPath(candidate);
}

async function requireDirectory(path: string, label: string): Promise<string> {
  const candidate = absolute(path);
  let information: Deno.FileInfo;
  try {
    information = await Deno.stat(candidate);
  } catch (error) {
    if (error instanceof Deno.errors.NotFound) {
      throw new Error(`${label} does not exist: ${candidate}`);
    }
    throw error;
  }
  if (!information.isDirectory) {
    throw new Error(`${label} is not a directory: ${candidate}`);
  }
  return await Deno.realPath(candidate);
}

async function requireBibliographySource(path: string): Promise<string> {
  const candidate = absolute(path);
  let information: Deno.FileInfo;
  try {
    information = await Deno.stat(candidate);
  } catch (error) {
    if (error instanceof Deno.errors.NotFound) {
      throw new Error(`Better CSL JSON export does not exist: ${candidate}`);
    }
    throw error;
  }
  if (information.isDirectory) {
    return await requireFile(
      join(candidate, "library.json"),
      "Better CSL JSON export",
    );
  }
  if (!information.isFile) {
    throw new Error(
      `Better CSL JSON export is not a file or directory: ${candidate}`,
    );
  }
  return await Deno.realPath(candidate);
}

async function parseBibliography(path: string): Promise<unknown[]> {
  let value: unknown;
  try {
    value = JSON.parse(await Deno.readTextFile(path));
  } catch (error) {
    if (error instanceof SyntaxError) {
      throw new Error(`Better CSL JSON export is malformed: ${path}`);
    }
    throw error;
  }
  if (!Array.isArray(value)) {
    throw new Error(`Better CSL JSON export must contain an array: ${path}`);
  }
  return value;
}

function setupOptions(args: string[]): SetupOptions {
  const options: SetupOptions = {};
  const names: Record<string, keyof SetupOptions> = {
    "--library": "library",
    "--zotero-data-dir": "zoteroDataDir",
    "--style": "style",
  };
  for (let index = 0; index < args.length; index++) {
    const argument = args[index];
    const equals = argument.indexOf("=");
    const flag = equals < 0 ? argument : argument.slice(0, equals);
    const name = names[flag];
    if (!name) throw new Error(`Unknown setup option: ${flag}`);
    const value = equals < 0 ? args[++index] : argument.slice(equals + 1);
    if (!value || value.startsWith("--")) {
      throw new Error(`${flag} expects a value`);
    }
    if (options[name]) throw new Error(`${flag} was provided more than once`);
    options[name] = value;
  }
  return options;
}

async function linkTarget(
  path: string,
  kind?: "file" | "directory",
): Promise<string | undefined> {
  try {
    const information = await Deno.lstat(path);
    if (!information.isSymlink) {
      throw new Error(
        `${relative(projectDir, path)} exists but is not a setup symlink`,
      );
    }
    const target = await Deno.stat(path);
    if (kind === "file" && !target.isFile) {
      throw new Error(`${relative(projectDir, path)} does not link to a file`);
    }
    if (kind === "directory" && !target.isDirectory) {
      throw new Error(
        `${relative(projectDir, path)} does not link to a directory`,
      );
    }
    return await Deno.realPath(path);
  } catch (error) {
    if (error instanceof Deno.errors.NotFound) return undefined;
    throw error;
  }
}

function ask(label: string, current?: string): string {
  const suffix = current ? ` [${current}]` : "";
  const answer = prompt(`${label}${suffix}:`)?.trim();
  if (answer) return answer;
  if (current) return current;
  throw new Error(
    `Missing ${label.toLowerCase()}; rerun setup with all three options`,
  );
}

async function removeFileIfPresent(path: string) {
  try {
    await Deno.remove(path);
  } catch (error) {
    if (!(error instanceof Deno.errors.NotFound)) throw error;
  }
}

async function acquireSetupLock(): Promise<Deno.FsFile> {
  await Deno.mkdir(dirname(setupLock), { recursive: true });
  const file = await Deno.open(setupLock, { create: true, write: true });
  try {
    await file.lock(true);
    return file;
  } catch (error) {
    file.close();
    throw error;
  }
}

async function releaseSetupLock(file: Deno.FsFile) {
  try {
    await file.unlock();
  } finally {
    file.close();
  }
}

async function replaceSymlinks(specifications: LinkSpec[]) {
  const changes: Array<
    LinkSpec & {
      temporary: string;
      backup: string;
      backedUp: boolean;
      installed: boolean;
    }
  > = [];

  try {
    for (const specification of specifications) {
      const current = await linkTarget(specification.destination);
      if (current === specification.target) continue;
      const identifier = crypto.randomUUID();
      const temporary = `${specification.destination}.tmp-${identifier}`;
      const backup = `${specification.destination}.backup-${identifier}`;
      await Deno.symlink(specification.target, temporary);
      changes.push({
        ...specification,
        temporary,
        backup,
        backedUp: false,
        installed: false,
      });
    }
  } catch (error) {
    for (const change of changes) {
      await removeFileIfPresent(change.temporary);
    }
    throw error;
  }

  let succeeded = false;
  try {
    for (const change of changes) {
      try {
        await Deno.lstat(change.destination);
        await Deno.rename(change.destination, change.backup);
        change.backedUp = true;
      } catch (error) {
        if (!(error instanceof Deno.errors.NotFound)) throw error;
      }
      await Deno.rename(change.temporary, change.destination);
      change.installed = true;
    }
    succeeded = true;
  } finally {
    if (!succeeded) {
      for (const change of [...changes].reverse()) {
        if (change.installed) await removeFileIfPresent(change.destination);
        if (change.backedUp) {
          await Deno.rename(change.backup, change.destination);
        }
      }
    }
    for (const change of changes) {
      await removeFileIfPresent(change.temporary);
      if (succeeded) await removeFileIfPresent(change.backup);
    }
  }

  for (const change of changes) {
    console.log(
      `Linked ${relative(projectDir, change.destination)} -> ${change.target}`,
    );
  }
}

async function configureReferencesUnlocked(args: string[]) {
  const options = setupOptions(args);
  await Deno.mkdir(referencesDir, { recursive: true });

  const currentLibrary = await linkTarget(bibliographyLink);
  const currentStyles = await linkTarget(zoteroStylesLink);
  const currentStyle = await linkTarget(styleLink);
  const interactive = Deno.stdin.isTerminal();

  const libraryInput = options.library || currentLibrary ||
    (interactive ? ask("Better CSL JSON export file or directory") : "");
  const dataInput = options.zoteroDataDir ||
    (currentStyles ? dirname(currentStyles) : "") ||
    (interactive ? ask("Zotero data directory") : "");
  const styleInput = options.style ||
    (currentStyle ? basename(currentStyle) : "") ||
    (interactive ? ask("Installed CSL style title, ID, or filename") : "");
  if (!libraryInput || !dataInput || !styleInput) {
    throw new Error(
      "Citation inputs are not configured; run bin/longform setup --library FILE_OR_DIR --zotero-data-dir DIR --style STYLE",
    );
  }

  const library = await requireBibliographySource(libraryInput);
  await parseBibliography(library);
  const dataDir = await requireDirectory(dataInput, "Zotero data directory");
  await requireFile(join(dataDir, "zotero.sqlite"), "Zotero database");
  const stylesDir = await requireDirectory(
    join(dataDir, "styles"),
    "Zotero styles directory",
  );
  const style = await selectStyle(stylesDir, styleInput);
  const selectedStyle = await requireFile(style.path, "Installed CSL style");

  const links: LinkSpec[] = [
    { target: library, destination: bibliographyLink },
    { target: stylesDir, destination: zoteroStylesLink },
    { target: selectedStyle, destination: styleLink },
  ];
  const parentLink = await dependentParentLink(stylesDir, style.source);
  await validateCslStyle(selectedStyle, parentLink);
  if (parentLink) {
    await Deno.mkdir(cslParentsDir, { recursive: true });
    links.push(parentLink);
  }

  await replaceSymlinks(links);
  console.log(`Bibliography source: ${library}`);
  console.log(`Citation style: ${style.title} (${style.filename})`);
}

async function configureReferences(args: string[]) {
  const lock = await acquireSetupLock();
  try {
    await configureReferencesUnlocked(args);
  } finally {
    await releaseSetupLock(lock);
  }
}

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
  if (files.length === 0) {
    throw new Error(
      "No chapters resolved from the Quarto project configuration",
    );
  }
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
  if (typeof value === "string" || typeof value === "number") {
    return String(value);
  }
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
    throw new Error(
      "longform.required-fonts must be a list of font family names",
    );
  }
  const fonts = value.map((font) =>
    typeof font === "string" ? font.trim() : ""
  );
  if (fonts.some((font) => font === "")) {
    throw new Error(
      "longform.required-fonts must contain only non-empty strings",
    );
  }
  return fonts;
}

// The Zettlr adapter lives in document/, so its paths are relative to that
// directory: author sources drop the document/ prefix and anything outside it
// (such as the CSL style) is reached with a leading ../.
function documentRelative(path: string): string {
  if (path === "") return path;
  return path.startsWith("document/")
    ? path.slice("document/".length)
    : `../${path}`;
}

function zettlrProject(data: Json) {
  const config = configFrom(data);
  return {
    sorting: "name-up",
    project: {
      title: scalar(object(config.book).title, "Longform document"),
      profiles: [],
      files: authorFiles(data).map(documentRelative),
      cslStyle: documentRelative(scalar(config.csl)),
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
  const path = join(projectDir, "document", ".ztr-directory");
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
  const bibliography = await parseBibliography(bibliographyPath);

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
        (manuscriptMetadataFiles.has(entry.name) ||
          entry.name === zettlrAdapterFile)
      ) {
        // Manuscript metadata (metadata.yml, chapters.yml) is author-owned, and
        // .ztr-directory is the generated Zettlr adapter for navigating
        // document/; both sit beside the prose even though they are not
        // Markdown.
      } else if (!entry.isFile || !entry.name.endsWith(".md")) {
        throw new Error(
          `Only author Markdown, ${manuscriptMetadataList}, and the generated ${zettlrAdapterFile} are allowed under document/: ${
            relative(authorDir, path)
          }`,
        );
      }
    }
  };
  await visit(authorDir);
}

async function check() {
  const configuredLinks: Array<[string, "file" | "directory"]> = [
    [bibliographyLink, "file"],
    [styleLink, "file"],
    [zoteroStylesLink, "directory"],
  ];
  for (const [path, kind] of configuredLinks) {
    if (!await linkTarget(path, kind)) {
      throw new Error("Citation inputs are missing; run bin/longform setup");
    }
  }
  const stylesDir = await linkTarget(zoteroStylesLink, "directory");
  if (!stylesDir) {
    throw new Error("Citation inputs are missing; run bin/longform setup");
  }
  const parentLink = await dependentParentLink(
    stylesDir,
    await Deno.readTextFile(styleLink),
  );
  if (parentLink) {
    const configuredParent = await linkTarget(parentLink.destination, "file");
    if (configuredParent !== parentLink.target) {
      throw new Error(
        "Dependent CSL parent link is missing or stale; run bin/longform setup",
      );
    }
  }
  await validateCslStyle(styleLink, parentLink);
  await syncHomeAdapter(true);
  const data = await inspect();
  const config = configFrom(data);
  const files = authorFiles(data);
  await checkAuthorDirectory();
  if (
    files.some((file) => !file.startsWith("document/") || !file.endsWith(".md"))
  ) {
    throw new Error(
      "Every author source must be a Markdown file under document/",
    );
  }
  for (const file of files) await Deno.stat(join(projectDir, file));

  const csl = scalar(config.csl);
  if (!csl) {
    throw new Error("quarto/project.yml must declare a configured CSL file");
  }
  if (csl !== "references/style.csl") {
    throw new Error(
      "quarto/project.yml must use the CSL link created by setup",
    );
  }
  const bibliographies = bibliographyPaths(config);
  if (
    bibliographies.length !== 1 ||
    bibliographies[0] !== "references/library.json"
  ) {
    throw new Error(
      "quarto/project.yml must use the bibliography link created by setup",
    );
  }
  const resourcePaths = strings(config["resource-path"]);
  if (
    resourcePaths.length !== citationResourcePaths.length ||
    resourcePaths.some((path, index) => path !== citationResourcePaths[index])
  ) {
    throw new Error(
      "quarto/project.yml must retain the citation resource paths used by setup",
    );
  }
  try {
    await Deno.stat(join(projectDir, csl));
  } catch (error) {
    if (error instanceof Deno.errors.NotFound) {
      throw new Error("Citation inputs are missing; run bin/longform setup");
    }
    throw error;
  }
  await sync(true);
  await checkBibliography(config, files);
  gfmTocDepth(config);
  requiredFonts(config);
  console.log(
    `Project: ${files.length} ordered source files, configuration valid`,
  );
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
  lines.push(
    yamlLine("bibliography", join(projectDir, bibliographyPaths(config)[0])),
  );
  lines.push(yamlLine("csl", join(projectDir, scalar(config.csl))));
  lines.push(yamlLine("shortcodes", [epigraphShortcode]));
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
  const excluded = new Set(["build", "index.md", "quarto", "_quarto.yml"]);
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
      epigraphExtension,
    );
    const extensionDestination = join(
      temporary,
      epigraphExtension,
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
        `--resource-path=${citationResourcePaths.join(":")}`,
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

const [command, ...arguments_] = Deno.args;
try {
  switch (command) {
    case "configure-references":
      await configureReferences(arguments_);
      break;
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
      const [argument] = arguments_;
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
      throw new Error(
        "Expected configure-references, sync, check, gfm, or info",
      );
  }
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  Deno.exit(1);
}
