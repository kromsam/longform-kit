local stringify = require("pandoc.utils").stringify

local function bool_attr(div, name, fallback)
  local value = div.attributes[name]
  if value == nil then return fallback end
  if value == "true" then return true end
  if value == "false" then return false end
  error("epigraph attribute " .. name .. " must be true or false")
end

local function parts(div)
  if #div.content ~= 2 or div.content[1].t ~= "BlockQuote" or
      div.content[2].t ~= "BlockQuote" then
    error("epigraphs require quotation and attribution blockquotes")
  end
  return div.content[1].content, div.content[2].content
end

local function latex_blocks(blocks)
  return pandoc.write(pandoc.Pandoc(blocks), "latex"):gsub("%s*$", "")
end

local function latex_epigraph(div, front)
  local quote, source = parts(div)
  local width = div.attributes.width or ".75"
  local numeric_width = tonumber(width)
  if numeric_width == nil or numeric_width <= 0 or numeric_width > 1 then
    error("epigraph width must be a decimal fraction greater than 0 and at most 1")
  end

  local output = pandoc.List()
  if front and bool_attr(div, "blank-before", false) then
    output:insert("\\clearpage\\thispagestyle{empty}\\mbox{}\\clearpage")
  end
  if bool_attr(div, "oddpage", front) then output:insert("\\cleardoublepage") end
  if front then output:insert("\\thispagestyle{empty}") end
  output:insert("\\setlength{\\epigraphwidth}{" .. width .. "\\textwidth}")
  output:insert("\\epigraph{" .. latex_blocks(quote) .. "}{" ..
    latex_blocks(source) .. "}")
  -- latex3/tagging-project#455 requires an explicit paragraph boundary after
  -- \epigraph.  Keep it even on the non-tagging PDF path so a later compatible
  -- PDF/UA renderer cannot reintroduce the paragraph-hook mismatch.
  output:insert("\\par")
  if not front and bool_attr(div, "separator", true) then
    output:insert("\\LongformEpigraphSeparator")
  end
  if bool_attr(div, "clear-after", false) then output:insert("\\clearpage") end
  return pandoc.RawBlock("latex", table.concat(output, "\n"))
end

local function docx_pagebreak()
  return pandoc.RawBlock("openxml",
    '<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
end

local function styled(blocks, class_name, style)
  return pandoc.Div(blocks,
    pandoc.Attr("", {class_name}, {["custom-style"] = style}))
end

local function docx_width_suffix(div)
  local width = tonumber(div.attributes.width or ".75")
  if width == nil then error("epigraph width must be numeric") end
  if math.abs(width - .60) < .001 then return "60" end
  if math.abs(width - .75) < .001 then return "75" end
  if math.abs(width - 1) < .001 then return "Full" end
  error("DOCX epigraph width must be .60, .75, or 1")
end

local function docx_epigraph(div, front)
  local quote, source = parts(div)
  local output = pandoc.List()
  local suffix = docx_width_suffix(div)
  local prefix = front and "Front Epigraph" or "Epigraph"
  local quote_style = prefix .. " Text " .. suffix
  local source_style = prefix .. " Source " .. suffix
  if not front and bool_attr(div, "separator", true) then
    source_style = source_style .. " Separator"
  end
  if front and bool_attr(div, "blank-before", false) then
    output:insert(docx_pagebreak())
  end
  if bool_attr(div, "pagebreak-before", front) then
    output:insert(docx_pagebreak())
  end
  if bool_attr(div, "leading-break", false) then
    local first = quote[1]
    if first and (first.t == "Para" or first.t == "Plain") then
      first.content:insert(1, pandoc.LineBreak())
    end
  end
  output:insert(styled(quote, "epigraph-quote", quote_style))
  output:insert(styled(source, "epigraph-source", source_style))
  if bool_attr(div, "pagebreak-after", front) then
    output:insert(docx_pagebreak())
  end
  return output
end

local function append_include_before(meta, blocks)
  local combined = pandoc.List()
  local existing = meta["include-before"]
  if existing then combined:extend(existing) end
  combined:extend(blocks)
  meta["include-before"] = pandoc.MetaBlocks(combined)
end

function Pandoc(doc)
  local body = pandoc.List()
  local front = nil
  local first_after_epigraph = false

  for _, block in ipairs(doc.blocks) do
    if block.t == "Div" and block.classes:includes("front-epigraph") then
      if front then error("only one front epigraph is allowed") end
      front = block
    elseif block.t == "Header" and block.level == 1 and
        stringify(block.content) == "" then
      -- A Quarto book synthesizes this chapter for an epigraph-only index.md.
      -- Once the front epigraph moves ahead of the TOC, the empty chapter must
      -- not consume a number or create a blank chapter-opening page.
    elseif block.t == "Div" and block.classes:includes("epigraph") then
      if FORMAT:match("latex") then
        body:insert(latex_epigraph(block, false))
      elseif FORMAT == "docx" then
        body:extend(docx_epigraph(block, false))
        first_after_epigraph = true
      else
        body:insert(block)
      end
    else
      if FORMAT == "docx" and first_after_epigraph and block.t == "Para" then
        body:insert(styled({block}, "first-after-epigraph", "First Paragraph"))
      else
        body:insert(block)
      end
      first_after_epigraph = false
    end
  end

  if front and FORMAT:match("latex") then
    append_include_before(doc.meta, {latex_epigraph(front, true)})
  elseif front and FORMAT == "docx" then
    append_include_before(doc.meta, docx_epigraph(front, true))
  elseif front then
    body:insert(1, front)
  end
  doc.blocks = body
  return doc
end
