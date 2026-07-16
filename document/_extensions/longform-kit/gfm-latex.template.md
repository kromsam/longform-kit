---
author:
$for(author-yaml)$
- $author-yaml$
$endfor$
date: $date-yaml$
degreetitle: $degreetitle-yaml$
institute: $institute-yaml$
lang: $lang-yaml$
reference-section-title: $reference-section-title-yaml$
studentnumber: $studentnumber-yaml$
subtitle: $subtitle-yaml$
supervisor: $supervisor-yaml$
title: $title-yaml$
---
$if(toc)$

$toc$
$endif$

$body$
