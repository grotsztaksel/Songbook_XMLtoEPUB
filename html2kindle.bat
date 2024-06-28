7z a -r songbook.zip output 
move songbook.zip songbook.epub
ebook-convert songbook.epub songbook.azw3  --duplicate-links-in-toc  --max-toc-links=0
ebook-convert songbook.epub songbook.pdf  --duplicate-links-in-toc  --max-toc-links=0

copy /y songbook.epub C:\Users\piotr\OneDrive\Books\Songbook
copy /y songbook.pdf C:\Users\piotr\OneDrive\Books\Songbook
copy /y songbook.pdf C:\Users\piotr\OneDrive\Books\Songbook

ebook-viewer songbook.azw3