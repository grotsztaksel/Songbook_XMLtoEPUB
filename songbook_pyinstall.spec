# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

a = Analysis(
    ['C:\\Users\\piotr\\Documents\\Songbook\\main.py'],
    pathex=['C:\\Users\\piotr\\Documents\\Songbook', 'C:\\Users\\piotr\\Documents\\Songbook\\scripts',
            'C:\\Users\\piotr\\Documents\\Songbook\\scripts\\config',
            'C:\\Users\\piotr\\Documents\\Songbook\\scripts\\tixi',
            'C:\\Users\\piotr\\Documents\\Songbook\\scripts\\tixi\\test',
            'C:\\Users\\piotr\\Documents\\Songbook\\scripts\\tixi\\xtixi',
            'C:\\Users\\piotr\\Documents\\Songbook\\scripts\\tools', 'C:\\Users\\piotr\\Documents\\Songbook\\test',
            'C:\\Users\\piotr\\Documents\\Songbook\\test\\test_config',
            'C:\\Users\\piotr\\Documents\\Songbook\\test\\test_tools'],
    binaries=[],
    datas=[
        ('C:\\Users\\piotr\\Documents\\Songbook\\scripts\\config\\source_schema.xsd', './scripts/config'),
        ('C:\\Users\\piotr\\Documents\\Songbook\\scripts\\config\\song_schema.xsd', './scripts/config'),
        ('C:\\Users\\piotr\\Documents\\Songbook\\scripts\\template\\acknowledgements.xhtml', './scripts/template'),
        ('C:\\Users\\piotr\\Documents\\Songbook\\scripts\\template\\metadata.opf', './scripts/template'),
        ('C:\\Users\\piotr\\Documents\\Songbook\\scripts\\template\\songbook.css', './scripts/template'),
        ('C:\\Users\\piotr\\Documents\\Songbook\\scripts\\template\\META-INF\\container.xml',
         './scripts/template/META-INF')
    ],
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
    name='__main__',
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
