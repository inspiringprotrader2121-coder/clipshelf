# Packaging

`clipshelf.spec` builds a standalone one-folder distribution with
[PyInstaller](https://pyinstaller.org/). Run it on the platform you target —
a Windows build has to be produced on Windows.

```bash
pip install pyinstaller
pyinstaller packaging/clipshelf.spec
```

The result lands in `dist/clipshelf/`:

- **Windows**: `clipshelf.exe` — a console binary you can wrap in an NSIS or
  Inno Setup installer, or ship as-is in a zip
- **macOS / Linux**: a `clipshelf` binary that runs the headless commands

The spec intentionally supports only the headless CLI for now; the tray UI
is still being built out. Reduce the final size by excluding unneeded
modules in the `Analysis` excludes list if you add dependencies.

## Versioning

The binary reports the version baked into `clipshelf.__version__`, so tag a
release before building if you want the exact number inside.