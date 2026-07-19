function Pandoc(document)
  for _, block in ipairs(document.blocks) do
    if block.t == 'Header' and block.level == 1 then
      -- Quarto synthesizes an empty level-one heading when an index adapter
      -- has content but no heading of its own. Mark only that first book
      -- heading as front matter so it cannot consume a chapter number.
      if #block.content == 0 then
        block.classes:insert('unnumbered')
        block.classes:insert('unlisted')
      end
      break
    end
  end
  return document
end
