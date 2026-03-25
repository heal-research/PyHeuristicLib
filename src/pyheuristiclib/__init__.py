import sys
import importlib.resources as pkg_resources
from pythonnet import load
load("coreclr")
import clr
import System

from . import InteroptUtil

# Load the DLL from the package
def load_dotnet_dll():
    dll_name = "HEAL.HeuristicLib.Core.dll"

    # Use importlib.resources to find the DLL inside the package
    with pkg_resources.path(pyheuristiclib, dll_name) as dll_path:
        abs_path = str(dll_path.resolve())
        System.Reflection.Assembly.LoadFrom(abs_path)
        clr.AddReference(dll_name.split(".")[0])
        print(f"[HeuristicLib] .NET DLL loaded from: {abs_path}")

load_dotnet_dll()