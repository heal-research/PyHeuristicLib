import os
import sys
import types
import importlib
import importlib.resources as pkg_resources
from pathlib import Path

from pythonnet import load
load("coreclr")

import clr
import System


DOTNET_ROOT_NS = "HEAL.HeuristicLib"
PYTHON_ROOT_NS = __name__


def load_dotnet_dll():
    dll_name = "HEAL.HeuristicLib.Core.dll"

    pkg = pkg_resources.files("pyheuristiclib.heuristiclib")
    dll_path = Path(str(pkg.joinpath(dll_name)))

    dll_dir = str(dll_path.parent)
    if dll_dir not in sys.path:
        sys.path.insert(0, dll_dir)

    os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")

    # Load assembly so pythonnet can import its namespaces
    clr.AddReference(str(dll_path))
    print(f"[HeuristicLib] .NET DLL loaded from: {dll_path}")

    return System.Reflection.Assembly.LoadFrom(str(dll_path))


def _ensure_module(module_name: str):
    module = sys.modules.get(module_name)
    if module is None:
        module = types.ModuleType(module_name)
        module.__package__ = module_name
        sys.modules[module_name] = module
    return module


def _ensure_module_hierarchy(module_name: str):
    parts = module_name.split(".")
    for i in range(1, len(parts) + 1):
        current_name = ".".join(parts[:i])
        current_mod = _ensure_module(current_name)

        if i > 1:
            parent_name = ".".join(parts[:i - 1])
            parent_mod = _ensure_module(parent_name)
            setattr(parent_mod, parts[i - 1], current_mod)

    return sys.modules[module_name]


def _get_exported_dotnet_namespaces(assembly):
    namespaces = set()

    try:
        types_ = assembly.GetExportedTypes()
    except System.Reflection.ReflectionTypeLoadException as ex:
        types_ = [t for t in ex.Types if t is not None]

    for t in types_:
        ns = t.Namespace
        if ns and ns.startswith(DOTNET_ROOT_NS):
            namespaces.add(ns)

    return sorted(namespaces)


def build_namespace_bridge(assembly):
    dotnet_namespaces = _get_exported_dotnet_namespaces(assembly)

    for dotnet_ns in dotnet_namespaces:
        py_ns = dotnet_ns.replace(DOTNET_ROOT_NS, PYTHON_ROOT_NS, 1)

        # Create pyheuristiclib.* module hierarchy
        py_module = _ensure_module_hierarchy(py_ns)

        # Import the real CLR namespace module exposed by pythonnet
        clr_module = importlib.import_module(dotnet_ns)

        exported = []
        for name in dir(clr_module):
            if name.startswith("_"):
                continue

            value = getattr(clr_module, name)
            setattr(py_module, name, value)
            exported.append(name)

        py_module.__all__ = sorted(set(exported))

    # Optional: expose top-level child modules in pyheuristiclib.__all__
    root_module = sys.modules[PYTHON_ROOT_NS]
    prefix = PYTHON_ROOT_NS + "."
    root_children = []

    for mod_name in list(sys.modules):
        if mod_name.startswith(prefix):
            remainder = mod_name[len(prefix):]
            if "." not in remainder:
                root_children.append(remainder)

    root_module.__all__ = sorted(set(getattr(root_module, "__all__", []) + root_children))


_assembly = load_dotnet_dll()
build_namespace_bridge(_assembly)

from . import InteroptUtil