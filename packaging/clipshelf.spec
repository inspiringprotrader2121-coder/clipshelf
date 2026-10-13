# PyInstaller spec for a standalone ClipShelf build (one-folder, console).
# Build it on the target platform: pyinstaller packaging/clipshelf.spec
# The Windows build produces dist/clipshelf/clipshelf.exe which can then be
# wrapped in the installer of your choice. See README.md in this folder.

a = Analysis(
    ["../clipshelf/__main__.py"],
    pathex=[".."],
    binaries=[],
    datas=[],
    hiddenimports=[],
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="clipshelf",
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="clipshelf",
)