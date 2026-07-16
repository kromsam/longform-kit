local stringify = require('pandoc.utils').stringify

local function meta_text(value, fallback)
  if value == nil then return fallback end
  local text = stringify(value)
  if text == '' then return fallback end
  return text
end

local function bool_attr(div, name, fallback)
  local value = div.attributes[name]
  if value == nil then return fallback end
  value = value:lower()
  if value == 'true' then return true end
  if value == 'false' then return false end
  error('Longform Kit: ' .. name .. ' must be true or false')
end

local function epigraph_parts(div)
  if #div.content ~= 2 then
    error('Longform Kit: epigraphs require one quotation block and one attribution block')
  end
  local quote = div.content[1]
  local source = div.content[2]
  if quote.t ~= 'BlockQuote' or source.t ~= 'BlockQuote' then
    error('Longform Kit: both epigraph blocks must use Markdown blockquote syntax')
  end
  return quote.content, source.content
end

local function latex_blocks(blocks)
  return pandoc.write(pandoc.Pandoc(blocks), 'latex'):gsub('%s*$', '')
end

local function latex_epigraph(div, front)
  local quote, source = epigraph_parts(div)
  local width = div.attributes.width or '.75'
  if not width:match('^%.?%d+$') then
    error('Longform Kit: epigraph width must be a decimal fraction')
  end

  local output = {}
  if front and bool_attr(div, 'blank-before', false) then
    table.insert(output, '\\clearpage\\thispagestyle{empty}\\mbox{}\\clearpage')
  end
  if bool_attr(div, 'oddpage', front) then
    table.insert(output, '\\cleardoublepage')
  end
  if front then table.insert(output, '\\thispagestyle{empty}') end
  table.insert(output, '\\setlength{\\epigraphwidth}{' .. width .. '\\textwidth}')
  table.insert(output, '\\epigraph{' .. latex_blocks(quote) .. '}{' .. latex_blocks(source) .. '}')
  if not front and bool_attr(div, 'separator', true) then
    table.insert(output, '\\chapterepigraphseparator')
  end
  if bool_attr(div, 'clear-after', false) then
    table.insert(output, '\\clearpage')
  end
  return pandoc.RawBlock('latex', table.concat(output, '\n'))
end

local function docx_pagebreak()
  return pandoc.RawBlock('openxml',
    '<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
end

local function styled_div(blocks, class_name, style)
  return pandoc.Div(blocks,
    pandoc.Attr('', {class_name}, {['custom-style'] = style}))
end

local function docx_epigraph(div, front)
  local quote, source = epigraph_parts(div)
  local output = pandoc.List()
  if bool_attr(div, 'pagebreak-before', front) then output:insert(docx_pagebreak()) end
  output:insert(styled_div(quote, 'epigraph-quote', 'Epigraph Text'))
  output:insert(styled_div(source, 'epigraph-source', 'Epigraph Source'))
  if bool_attr(div, 'pagebreak-after', front) then output:insert(docx_pagebreak()) end
  return output
end

local function plain_epigraph(div)
  local quote, source = epigraph_parts(div)
  local output = pandoc.List(quote)
  output:extend(source)
  return output
end

local function transform_epigraph(div, front)
  if FORMAT:match('latex') then return {latex_epigraph(div, front)} end
  if FORMAT == 'docx' then return docx_epigraph(div, front) end
  return plain_epigraph(div)
end

local function toc_field(meta)
  local title = meta_text(meta['toc-title'], 'Contents')
  local depth = tonumber(meta_text(meta['toc-depth'], '2')) or 2
  local escaped_title = title:gsub('&', '&amp;'):gsub('<', '&lt;'):gsub('>', '&gt;')
  local xml = table.concat({
    '<w:sdt>',
    '<w:sdtPr><w:docPartObj><w:docPartGallery w:val="Table of Contents"/>',
    '<w:docPartUnique/></w:docPartObj></w:sdtPr>',
    '<w:sdtContent>',
    '<w:p><w:pPr><w:pStyle w:val="TOCHeading"/></w:pPr>',
    '<w:r><w:t xml:space="preserve">' .. escaped_title .. '</w:t></w:r></w:p>',
    '<w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/>',
    '<w:instrText xml:space="preserve">TOC \\o &quot;1-' .. depth ..
      '&quot; \\h \\z \\u</w:instrText>',
    '<w:fldChar w:fldCharType="separate"/>',
    '<w:fldChar w:fldCharType="end"/></w:r></w:p>',
    '</w:sdtContent></w:sdt>'
  })
  return pandoc.RawBlock('openxml', xml)
end

local function bibliography_breaks(meta)
  if meta.longform == nil then return 1 end
  return tonumber(meta_text(meta.longform['bibliography-pagebreaks'], '1')) or 1
end

local function style_bibliography(div)
  if div.identifier ~= 'refs' then return div end
  return div:walk({
    Div = function(entry)
      if entry.classes:includes('csl-entry') then
        entry.attributes['custom-style'] = 'Bibliography'
      end
      return entry
    end
  })
end

local function append_include_before(meta, blocks)
  local existing = meta['include-before']
  local combined = pandoc.List()
  if existing and existing.t == 'MetaBlocks' then combined:extend(existing) end
  combined:extend(blocks)
  meta['include-before'] = pandoc.MetaBlocks(combined)
end

local function format_list(value)
  local formats = {}
  if value == nil then return formats end
  for item in stringify(value):gmatch('[^,%s]+') do formats[item] = true end
  return formats
end

local function apply_gfm_conditionals(doc)
  if not FORMAT:match('gfm') then return doc end
  return doc:walk({
    Div = function(div)
      local formats = format_list(div.attributes['when-format'])
      if div.classes:includes('content-visible') then
        if formats.gfm or formats.markdown then return div.content end
        return {}
      end
      if div.classes:includes('content-hidden') then
        if formats.gfm or formats.markdown then return {} end
        return div.content
      end
      return nil
    end
  })
end

local function meta_latex(value)
  if value == nil or stringify(value) == '' then return '' end
  local ok, rendered = pcall(function()
    return pandoc.write(pandoc.Pandoc({pandoc.Plain(value)}), 'latex'):gsub('%s*$', '')
  end)
  if ok then return rendered end
  return pandoc.write(
    pandoc.Pandoc({pandoc.Plain({pandoc.Str(stringify(value))})}),
    'latex'
  ):gsub('%s*$', '')
end

local function inject_latex_title_metadata(meta)
  if not FORMAT:match('latex') or meta.longform == nil then return end
  local commands = pandoc.List()
  local fields = {
    {'student-number', 'longformstudentnumber'},
    {'degree-title', 'longformdegreetitle'},
    {'supervisor', 'longformsupervisor'},
    {'institute', 'longforminstitute'},
  }
  for _, field in ipairs(fields) do
    local value = meta_latex(meta.longform[field[1]])
    if value ~= '' then commands:insert('\\' .. field[2] .. '{' .. value .. '}') end
  end
  if #commands == 0 then return end
  local raw = pandoc.RawBlock('latex',
    '\\AtBeginDocument{\n' .. table.concat(commands, '\n') .. '\n}')
  local includes = meta['header-includes'] or pandoc.MetaList({})
  includes:insert(pandoc.MetaBlocks({raw}))
  meta['header-includes'] = includes
end

function Pandoc(doc)
  inject_latex_title_metadata(doc.meta)
  doc = apply_gfm_conditionals(doc)
  doc = pandoc.utils.citeproc(doc)
  local body = pandoc.List()
  local front = nil

  for _, block in ipairs(doc.blocks) do
    if block.t == 'Div' and block.classes:includes('front-epigraph') then
      if front ~= nil then error('Longform Kit: only one front epigraph is allowed') end
      front = block
    elseif block.t == 'Header' and block.level == 1 and stringify(block.content) == '' then
      -- Quarto books synthesize an empty chapter for an epigraph-only index.qmd.
    elseif block.t == 'Div' and block.classes:includes('epigraph') then
      body:extend(transform_epigraph(block, false))
    else
      body:insert(block)
    end
  end

  if FORMAT == 'docx' then
    local output = pandoc.List()
    if front then output:extend(transform_epigraph(front, true)) end
    output:insert(toc_field(doc.meta))
    if not front then output:insert(docx_pagebreak()) end

    local breaks = bibliography_breaks(doc.meta)
    for index, block in ipairs(body) do
      local next_block = body[index + 1]
      if block.t == 'Header' and next_block and next_block.t == 'Div' and
          next_block.identifier == 'refs' then
        for _ = 1, breaks do output:insert(docx_pagebreak()) end
      end
      if block.t == 'Div' and block.identifier == 'refs' then
        output:insert(style_bibliography(block))
      else
        output:insert(block)
      end
    end
    doc.blocks = output
    doc.meta.toc = false
    doc.meta['table-of-contents'] = false
  else
    if front then
      local transformed = transform_epigraph(front, true)
      if FORMAT:match('latex') then
        doc.meta['longform-front-epigraph'] = pandoc.MetaBlocks(transformed)
      else
        append_include_before(doc.meta, transformed)
      end
    end
    doc.blocks = body
  end

  return doc
end
