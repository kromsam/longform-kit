# Optional font sources

Font binaries are deliberately not committed. When
`LONGFORM_EMBED_DOCX_FONTS=1` is set, the feature accepts only the six EB
Garamond 1.001 OTF files and SHA-256 checksums recorded in `policy.py`.

The fonts are available from the EB Garamond project and are licensed under
the SIL Open Font License 1.1. Set `LONGFORM_EB_GARAMOND_DIR` to an absolute
directory containing those checked files when they are not installed at
`/usr/share/fonts/EBGaramond12-otf`.
