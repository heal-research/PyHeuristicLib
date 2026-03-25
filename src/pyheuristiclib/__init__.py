import sys
import importlib.resources as pkg_resources
from pathlib import Path
from pythonnet import load
load("coreclr")
import clr
import System
from . import InteroptUtil

def load_dotnet_dll():
    dll_name = "HEAL.HeuristicLib.Core.dll"

    # Modern API (works in 3.9+, not deprecated)
    pkg = pkg_resources.files("pyheuristiclib.heuristiclib")
    dll_path = Path(str(pkg.joinpath(dll_name)))

    # Add the DLL directory to PATH so .NET can resolve dependencies
    dll_dir = str(dll_path.parent)
    if dll_dir not in sys.path:
        sys.path.insert(0, dll_dir)
    
    # Also add to the process PATH for native DLL resolution
    import os
    os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")

    System.Reflection.Assembly.LoadFrom(str(dll_path))
    clr.AddReference(dll_name.removesuffix(".dll"))
    print(f"[HeuristicLib] .NET DLL loaded from: {dll_path}")

load_dotnet_dll()