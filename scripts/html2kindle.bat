7z a -r ..\songbook.zip ..\output 
move ..\songbook.zip ..\songbook.epub
ebook-convert ..\songbook.epub ..\songbook.azw3  --duplicate-links-in-toc  --max-toc-links=0
@pause