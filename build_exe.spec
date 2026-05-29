# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec файл для DraftAssistant.
Сборка: pyinstaller build_exe.spec
"""
from pathlib import Path

PROJECT_DIR = Path(SPECPATH)

block_cipher = None

# Файлы и папки которые нужно положить рядом с .exe
# (или внутрь --onefile архива)
datas = []

# Иконка
icon_path = PROJECT_DIR / "assets" / "app_icon.ico"
if icon_path.exists():
    datas.append((str(icon_path), "assets"))

# Кэш данных — кладём если есть, чтобы при первом запуске уже было что показать
cache_dir = PROJECT_DIR / "cache"
if cache_dir.exists():
    for cf in cache_dir.glob("*.json"):
        datas.append((str(cf), "cache"))


a = Analysis(
    ["main.py"],
    pathex=[str(PROJECT_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",
        "PIL.ImageFont",
        "requests",
        "numpy",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Исключаем тяжёлые библиотеки которые не используются
    excludes=[
        "matplotlib",
        "scipy",
        "pandas",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
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
    console=False,  # без чёрной консоли
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.exists() else None,
)
