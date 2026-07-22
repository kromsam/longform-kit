local stringify = require("pandoc.utils").stringify
local pandoc_type = require("pandoc.utils").type

local function metadata_map(value, name)
  if value == nil or pandoc_type(value) ~= "table" then
    error(name .. " must be a metadata object")
  end
  return value
end

local function value_inlines(value)
  if value == nil then return nil end
  if pandoc_type(value) == "Inlines" then return pandoc.Inlines(value) end
  return pandoc.Inlines({pandoc.Str(stringify(value))})
end

local function labelled(label, value, separator)
  local content = value_inlines(label)
  content:insert(pandoc.Str(separator))
  content:extend(value_inlines(value))
  return content
end

local function styled_paragraph(content, class_name, style_name)
  return pandoc.Div(
    {pandoc.Para(content)},
    pandoc.Attr("", {class_name}, {["custom-style"] = style_name})
  )
end

local function append_include_before(meta, blocks)
  local combined = pandoc.List()
  local existing = meta["include-before"]
  if existing then combined:extend(existing) end
  combined:extend(blocks)
  meta["include-before"] = pandoc.MetaBlocks(combined)
end

function Meta(meta)
  local config = metadata_map(meta["academic-title-page"], "academic-title-page")
  local labels = config.labels
  if labels == nil then
    labels = {}
    config.labels = labels
  else
    labels = metadata_map(labels, "academic-title-page.labels")
  end
  labels["student-number"] = labels["student-number"] or
    pandoc.MetaString("Student number")
  labels.supervisor = labels.supervisor or
    pandoc.MetaString("Under supervision of")
  meta["academic-title-page"] = config

  if FORMAT ~= "docx" then return meta end
  local blocks = pandoc.List()
  if config["student-number"] ~= nil then
    blocks:insert(styled_paragraph(
      labelled(labels["student-number"], config["student-number"], ": "),
      "student-number",
      "Student Number"
    ))
  end
  if config.degree ~= nil then
    blocks:insert(styled_paragraph(value_inlines(config.degree), "degree", "Degree"))
  end
  if config.supervisor ~= nil then
    blocks:insert(styled_paragraph(
      labelled(labels.supervisor, config.supervisor, " "),
      "supervisor",
      "Supervisor"
    ))
  end
  if config.institute ~= nil then
    blocks:insert(styled_paragraph(
      value_inlines(config.institute), "institute", "Institute"
    ))
  end
  append_include_before(meta, blocks)
  return meta
end
