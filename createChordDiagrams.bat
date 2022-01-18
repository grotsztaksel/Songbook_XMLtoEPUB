cd "C:\Users\piotr\Documents\Songs XML"
@echo off
set PY="C:\Users\piotr\AppData\Local\Programs\Python\Python39"
set PATH="%PY%;%PATH%"
set PATH="%PY%\DLLs;%PATH%"
set PATH="%PY%\Lib;%PATH%"
set PATH="%PY%\Lib\site-packages;%PATH%"
set PATH="C:\Users\piotr\Documents\ChordPainter;%PATH%"
set PATH="C:\Users\piotr\Documents\ChordPainter\Instruments;%PATH%"
%PY%\python.exe "C:\Users\piotr\Documents\ChordPainter\generate_htmls.py"
@echo on
move "C:\Users\piotr\Documents\ChordPainter\*.xhtml" "C:\Users\piotr\Documents\Songs XML"
copy "C:\Users\piotr\Documents\ChordPainter\HTML\*.css" "C:\Users\piotr\Documents\Songs XML"
move "C:\Users\piotr\Documents\ChordPainter\img\*.png" "C:\Users\piotr\Documents\Songs XML\img"

cd "C:\Users\piotr\Documents\Songs XML"
powershell -Command "(gc guitar_C_major.xhtml) -replace '<title>C</title>', '<title>Akordy na gitarze i ukulele</title>' | Out-File guitar_C_major.xhtml"
powershell -Command "(gc banjo_C_major.xhtml) -replace '<title>C</title>', '<title>Akordy na banjo</title>' | Out-File banjo_C_major.xhtml"