cd "C:\Users\piotr\Documents\Songs XML\SeparateFiles"
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
move "C:\Users\piotr\Documents\ChordPainter\*.xhtml" "C:\Users\piotr\Documents\Songs XML\SeparateFiles"
move "C:\Users\piotr\Documents\ChordPainter\img\*.png" "C:\Users\piotr\Documents\Songs XML\SeparateFiles\img"