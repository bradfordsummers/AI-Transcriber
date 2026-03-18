# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for AI Transcriber.

Build with:  pyinstaller main.spec
Output:      dist/AI-Transcriber.exe
"""

import os
import customtkinter

# Locate customtkinter's package directory so we can bundle its assets
ctk_path = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        # Bundle customtkinter theme/assets
        (ctk_path, "customtkinter"),
    ],
    hiddenimports=[
        "customtkinter",
        "scipy.io.wavfile",
        "scipy._lib",
        "numpy",
        "sounddevice",
        "openai",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AI-Transcriber",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,           # No console window — windowed mode
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
