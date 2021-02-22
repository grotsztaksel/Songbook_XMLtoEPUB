# Songbook XML to ePub

This project offers a suite of tools allowing automated transformation of a songbook defined in an XML file, or set of files into a form of EPUB compliant HTML files*. These can then be converted into an eBook by other tools**. 


## Requirements

* [Tixi](https://github.com/DLR-SC/tixi) - a fast and simple XML interface library developed in German Aerospace Center  \
 **NOTE:** as of Feb 2022, Python 3.9 is not supported by Tixi
* [XTixi](https://github.com/grotsztaksel/XTixi) - A set of Python utilities expanding the functionality of the Tixi library. It is added as a submodule to this repository, so should be checked out together with it.

## Environemnt
Due to Tixi not yet supporting Python 3.9, an older (I worked with 3.7) version should be used. It can be compiled from source obtained from [Python.org](https://www.python.org/downloads/release/python-3710/). Another way, simpler than compilation from source, is setting up an environment in [Anaconda](https://www.anaconda.com/)

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
 \* The "EPUB compliant" means that an example EPUB file has been reverse engineered and a set of files essential for successful creation of an eBook has been defined.

** I found [Calibre](https://github.com/kovidgoyal/calibre) particularly useful: note it has a command line mode that can easily be used in an automated way aling with this 
