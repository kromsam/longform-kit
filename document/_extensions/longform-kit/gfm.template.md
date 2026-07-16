$if(title)$
# $title$
$endif$
$if(subtitle)$

*$subtitle$*
$endif$
$if(author)$

$for(author)$$author$$sep$; $endfor$
$endif$
$if(date)$

$date$
$endif$
$for(include-before)$

$include-before$
$endfor$
$if(toc)$

$toc$
$endif$

$body$
