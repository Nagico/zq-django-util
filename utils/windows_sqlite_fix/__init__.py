import os
import shutil
import sys
from pathlib import Path

import colorama
import requests

work_dir = os.path.dirname(os.path.abspath(__file__))


def get_dll():
    import platform
    import zipfile

    print(
        f"Copying sqlite3.dll to the current directory: {os.getcwd()} ... ",
        end="",
    )

    filename = (
        "sqlite-dll-win64-x64-3400100.zip"
        if platform.architecture()[0] == "64bit"
        else "sqlite-dll-win32-x86-3400100.zip"
    )

    url = "https://www.sqlite.org/2022/" + filename

    src = os.path.join(work_dir, "sqlite.zip")
    try:
        with open(src, "wb") as f_out:
            resp = requests.get(url, verify=False)  # nosec
            f_out.write(resp.content)
    except Exception as e:
        print(
            colorama.Fore.LIGHTRED_EX
            + f"\nCan't download sqlite.zip: {e}\nPlease, download it manually and extract in the current directory:\n"
            + url
        )
        print(colorama.Fore.WHITE)
        exit(-1)

    with zipfile.ZipFile(src, "r") as zip_ref:
        zip_ref.extractall(".", members=["sqlite3.dll"])

    print("finished")
    print(colorama.Fore.WHITE)


def check_fix(force: bool = False) -> bool:
    """Copy sqlite.dll to the current directory and use it"""

    if force:
        return True

    # check if it is not on windows
    if sys.platform != "win32":
        print("This script is for Windows only")
        return False
    print(f"Current platform is {sys.platform}, apply sqlite fix")

    # check sqlite version
    import sqlite3

    v = sqlite3.sqlite_version_info
    if v[0] >= 3 and v[1] >= 35:
        print("SQLite version is OK: " + sqlite3.sqlite_version)
        return False

    # check python version and warn
    print(
        f"python version: {sys.version_info.major} sqlite minor version: {sys.version_info.minor}"
    )
    if sys.version_info.major == 3 and sys.version_info.minor in [6, 7, 8]:
        print(
            "\n"
            + colorama.Fore.LIGHTYELLOW_EX
            + "You are on "
            + colorama.Fore.LIGHTRED_EX
            + f"Windows Python {sys.version_info.major}.{sys.version_info.minor}.\n"
            + colorama.Fore.LIGHTYELLOW_EX
            + f"This Python version uses SQLite "
            f"{colorama.Fore.LIGHTRED_EX}{v[0]}.{v[1]}.{v[2]} "
            + colorama.Fore.LIGHTYELLOW_EX
            + "which does not support JSON Field.\n"
            + "Read more about this issue: "
            + colorama.Fore.LIGHTWHITE_EX
            + "https://code.djangoproject.com/wiki/JSON1Extension [Windows section]\n"
        )

        return True

    print(colorama.Fore.WHITE)


if __name__ == "__main__":
    if not check_fix(True):
        print("No need to fix sqlite, exit...")
        exit(0)
    get_dll()
    python_dir = Path(sys.executable).parent
    dll_dir = python_dir / "DLLs"
    if not dll_dir.exists():
        dll_dir.mkdir()

    dll_path = dll_dir / "sqlite3.dll"
    shutil.copy("sqlite3.dll", dll_path)
