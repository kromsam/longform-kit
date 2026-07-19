local input = assert(arg[1], "missing input DOCX")
local output = assert(arg[2], "missing output DOCX")

local function read_file(path)
  local file = assert(io.open(path, "rb"))
  local contents = assert(file:read("*a"))
  file:close()
  return contents
end

local function write_file(path, contents)
  local file = assert(io.open(path, "wb"))
  assert(file:write(contents))
  assert(file:close())
end

local function strip_custom_paths(xml)
  return xml:gsub("<property%s.-</property>", function(property)
    if property:match('name%s*=%s*["\']bibliography["\']') or
       property:match('name%s*=%s*["\']csl["\']') then
      return ""
    end
    return property
  end)
end

local function strip_stale_statistics(xml)
  local names = {
    "TotalTime",
    "Pages",
    "Words",
    "Characters",
    "CharactersWithSpaces",
    "Lines",
    "Paragraphs",
  }
  for _, name in ipairs(names) do
    xml = xml:gsub("<" .. name .. "[^>]*>[%s%S]-</" .. name .. "%s*>", "")
  end
  return xml
end

local archive = pandoc.zip.Archive(read_file(input))
local entries = {}
local found_custom = false
local found_app = false
for _, entry in ipairs(archive.entries) do
  if entry.path == "docProps/custom.xml" then
    found_custom = true
    entries[#entries + 1] = pandoc.zip.Entry(
      entry.path,
      strip_custom_paths(entry:contents()),
      entry.modtime
    )
  elseif entry.path == "docProps/app.xml" then
    found_app = true
    entries[#entries + 1] = pandoc.zip.Entry(
      entry.path,
      strip_stale_statistics(entry:contents()),
      entry.modtime
    )
  else
    entries[#entries + 1] = entry
  end
end
assert(found_custom, "DOCX is missing docProps/custom.xml")
assert(found_app, "DOCX is missing docProps/app.xml")
write_file(output, pandoc.zip.Archive(entries):bytestring())
