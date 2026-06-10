# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec файл для DraftAssistant (pywebview).
Сборка: pyinstaller build_exe.spec
"""
from pathlib import Path

PROJECT_DIR = Path(SPECPATH)

block_cipher = None

datas = []

icon_path = PROJECT_DIR / "assets" / "app_icon.ico"
if icon_path.exists():
    datas.append((str(icon_path), "assets"))

hero_icons_dir = PROJECT_DIR / "assets" / "hero_icons"
if hero_icons_dir.exists():
    datas.append((str(hero_icons_dir), "assets/hero_icons"))

cache_dir = PROJECT_DIR / "cache"
if cache_dir.exists():
    for cf in cache_dir.glob("*.json"):
        datas.append((str(cf), "cache"))

web_dir = PROJECT_DIR / "ui" / "web"
if web_dir.exists():
    datas.append((str(web_dir), "ui/web"))


a = Analysis(
    ["main.py"],
    pathex=[str(PROJECT_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "webview",
        "webview.platforms",
        "webview.platforms.winforms",
        "webview.platforms.cef",
        "clr_loader",
        "pythonnet",
        "bottle",
        "proxy_tools",
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",
        "PIL.ImageFont",
        "PIL.ImageTk",
        "requests",
        "numpy",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "scipy",
        "pandas",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "tkinter",
        "ttkbootstrap",
        "test",
        "unittest",
        "pydoc_data",
    ],
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
    name="DraftAssistant",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.exists() else None,
)
