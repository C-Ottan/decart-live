"""PyInstaller compilation script for DECART LIVE PRO standalone executable.
Ensures 100% complete bundling of Python's standard Tkinter, Tcl/Tk DLLs,
CustomTkinter, and Reactor SDK runtime.
"""

import os
import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent


def find_python_base():
    """Find the base Python installation where Tkinter/Tcl resides."""
    try:
        import _tkinter
        dll_dir = Path(_tkinter.__file__).parent
        base_dir = dll_dir.parent
        return base_dir, dll_dir
    except Exception:
        base_dir = Path(sys.base_prefix)
        return base_dir, base_dir / "DLLs"


def build():
    print("=" * 65)
    print("  COMPILING DECART LIVE PRO -> DecartLivePro.exe")
    print("=" * 65)

    base_dir, dll_dir = find_python_base()
    tcl_dir = base_dir / "tcl"
    lib_tkinter = base_dir / "Lib" / "tkinter"

    print(f"[*] Base Python:  {base_dir}")
    print(f"[*] DLLs Dir:     {dll_dir}")
    print(f"[*] Tcl/Tk Dir:   {tcl_dir}")
    print(f"[*] Tkinter Dir:  {lib_tkinter}")

    pyinstaller_exe = ROOT_DIR / "venv" / "Scripts" / "pyinstaller.exe"
    if not pyinstaller_exe.exists():
        pyinstaller_exe = "pyinstaller"

    cmd = [
        str(pyinstaller_exe),
        "--name=DecartLivePro",
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
        # Include base Python Lib in search paths so tkinter submodules are discovered
        f"--paths={base_dir / 'Lib'}",
        f"--paths={base_dir / 'DLLs'}",
        # Explicit hidden imports for all Tkinter subsystems
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=tkinter.filedialog",
        "--hidden-import=tkinter.font",
        "--hidden-import=tkinter.colorchooser",
        "--hidden-import=tkinter.commondialog",
        "--hidden-import=tkinter.constants",
        "--hidden-import=tkinter.dialog",
        "--hidden-import=tkinter.simpledialog",
        "--hidden-import=_tkinter",
        # Package collections
        "--collect-all=customtkinter",
        "--collect-all=reactor_sdk",
        # Asset files
        "--add-data=assets;assets",
    ]

    # Directly bundle the tkinter package directory
    if lib_tkinter.exists():
        cmd.append(f"--add-data={lib_tkinter};tkinter")

    # Directly bundle the entire tcl data directory
    if tcl_dir.exists():
        cmd.append(f"--add-data={tcl_dir};tcl")

    # Directly bundle the Tkinter C extension and Tcl/Tk core DLLs
    _tkinter_pyd = dll_dir / "_tkinter.pyd"
    if _tkinter_pyd.exists():
        cmd.append(f"--add-binary={_tkinter_pyd};.")

    tcl_dll = dll_dir / "tcl86t.dll"
    if tcl_dll.exists():
        cmd.append(f"--add-binary={tcl_dll};.")

    tk_dll = dll_dir / "tk86t.dll"
    if tk_dll.exists():
        cmd.append(f"--add-binary={tk_dll};.")

    cmd.append("app.py")

    print("\n[*] Running PyInstaller with complete Tkinter runtime bundle...")
    proc = subprocess.run(cmd, cwd=str(ROOT_DIR))

    if proc.returncode == 0:
        exe_path = ROOT_DIR / "dist" / "DecartLivePro.exe"
        print("\n" + "=" * 65)
        print(" [SUCCESS] Standalone Executable Created with Full Tkinter Runtime!")
        print(f" Executable: {exe_path}")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f" File Size: {size_mb:.2f} MB")
            # Also copy directly to Desktop for quick deployment
            try:
                import shutil
                desktop_target = Path.home() / "Desktop" / "DecartLivePro.exe"
                shutil.copy2(exe_path, desktop_target)
                print(f" [*] Copied fresh binary to Desktop: {desktop_target}")
            except Exception as e:
                print(f" [!] Could not copy to Desktop: {e}")
        print("=" * 65)
    else:
        print("\n[ERROR] Build exited with return code:", proc.returncode)
        sys.exit(proc.returncode)


if __name__ == "__main__":
    build()
