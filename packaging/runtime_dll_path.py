"""Prioritize bundled DLLs before importing Qt on Windows."""

from __future__ import annotations

import os
import sys


_dll_directory_handle = None

if sys.platform == "win32" and getattr(sys, "frozen", False):
    bundle_dir = str(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)))
    os.environ["PATH"] = bundle_dir + os.pathsep + os.environ.get("PATH", "")
    if hasattr(os, "add_dll_directory"):
        _dll_directory_handle = os.add_dll_directory(bundle_dir)

