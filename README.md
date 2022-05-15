# Songbook XML to ePub

This project offers a suite of tools allowing automated transformation of a songbook defined in an XML file, or set of files into a form of EPUB compliant HTML files[^1]. These can then be converted into an eBook by other tools[^2]. I found PDF files inconvinient on my e-Book reader and I wanted to store my collections of songs in a repository[^3], so that the whole songbook can easily be updated with regard to content and behavior.

The tools allow the resulting songbook have a table of contents, alphabetic indexes of songs and authors, links between songs, chords presented in a prefered way (above the verse lines, or beside it) etc. It even allows adding custom HTML pages to the compilation: this was meant as a way to add pages formatted differently than a song - some notes, interesting history associated with the song; I used this feature to contain tables of guitar chords at the end of the songbook; theoretically one could use it to ePub the entire collection of Shakespeare's works, should more convinient tools for such purposes be not available.


## Requirements

* [Tixi](https://github.com/DLR-SC/tixi) - a fast and simple XML interface library developed in German Aerospace Center  \
 **NOTE:** as of Feb 2021, Python 3.9 was not supported by Tixi; newer releases should have fixed this issue.
* [XTixi](https://github.com/grotsztaksel/XTixi) - A set of Python utilities expanding the functionality of the Tixi library. It is added as a submodule to this repository, so should be checked out together with it.

## Setup for dummies (Like myself)
1. Download & install [Anaconda](https://www.anaconda.com/)
1. Launch Anaconda Command Prompt (on Windows) and type:
```
conda create --name py37 python=3.7 pip
conda activate py37
```
1. Install Tixi following [these](https://anaconda.org/DLR-SC/tixi3) instructions:
```
conda install -c dlr-sc tixi3
```
 
### Footnotes 
[^1]:I am not familiar with the whole ePub standard or requirements. "EPUB compliant" means that I reverse engineered an example EPUB file and defined a set of files essential for successful creation of an eBook looking and behaving good on my Kindle Paperwhite.

[^2]: I found [Calibre](https://github.com/kovidgoyal/calibre) particularly useful: note it has a command line mode that can easily be used in an automated way along with this 

[^3]: To stay on the safe side of the copyrights of the song authors I will not publish my collection of songs.
