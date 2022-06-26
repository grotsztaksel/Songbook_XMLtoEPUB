# -*- mode: python ; coding: utf-8 -*-

import argparse
import glob
import logging
import os

# Have to use argparser to figure out the src directory. Using __file__ is not possible here!
parser = argparse.ArgumentParser()
parser.add_argument('input', type=argparse.FileType('r'))
args = parser.parse_args()
src = os.path.dirname(args.input.buffer.raw.name)

# include all files that are in template directory
template_files = [item for item in glob.glob(os.path.join(src, "src", "template") + "/**/*", recursive=True)
                  if os.path.isfile(item)]
# include all xsd files
xsd_files = glob.glob(src + "/**/*.xsd", recursive=True)

datas = [(file, os.path.dirname(os.path.relpath(file, src))) for file in template_files + xsd_files]
logging.debug(f"datas={datas}")

block_cipher = None

a = Analysis(
    [os.path.join(src, 'main.py')],
    pathex=[src,
            os.path.join(src, 'src', ),
            os.path.join(src, 'src', 'config', ),
            os.path.join(src, 'src', 'tixi', 'xtixi'),
            os.path.join(src, 'src', 'tools')
            ],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='songebook',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
