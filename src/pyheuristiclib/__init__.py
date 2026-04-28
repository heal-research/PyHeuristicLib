import os
import sys
import types
import importlib
import importlib.resources as pkg_resources
from pathlib import Path

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("pyheuristiclib")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

from pythonnet import load
load("coreclr")

import clr
import System




DOTNET_ROOT_NS = "HEAL.HeuristicLib"
PYTHON_ROOT_NS = __name__


def load_dotnet_dlls():
    pkg = pkg_resources.files("pyheuristiclib.heuristiclib")
    dll_dir = Path(str(pkg)).resolve()

    if str(dll_dir) not in sys.path:
        sys.path.insert(0, str(dll_dir))

    os.environ["PATH"] = str(dll_dir) + os.pathsep + os.environ.get("PATH", "")

    assemblies = []

    for dll_path in sorted(dll_dir.glob("*.dll")):
        try:
            clr.AddReference(str(dll_path))
            assembly = System.Reflection.Assembly.LoadFrom(str(dll_path))
            assemblies.append(assembly)
            print(f"[HeuristicLib] .NET DLL loaded from: {dll_path}")
        except Exception as ex:
            print(f"[HeuristicLib] Could not load {dll_path}: {ex}")

    return assemblies


def _ensure_module(module_name: str):
    module = sys.modules.get(module_name)

    if module is None:
        module = types.ModuleType(module_name)
        module.__package__ = module_name

        # Mark synthetic namespace modules as packages
        module.__path__ = []

        sys.modules[module_name] = module

    return module


def _ensure_module_hierarchy(module_name: str):
    parts = module_name.split(".")

    for i in range(2, len(parts) + 1):  # start at 2, skip root pyheuristiclib
        current_name = ".".join(parts[:i])
        current_mod = _ensure_module(current_name)

        parent_name = ".".join(parts[:i - 1])
        parent_mod = sys.modules[parent_name]
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

DEBUG_BRIDGE = os.environ.get("PYHEURISTICLIB_DEBUG_BRIDGE") == "1"
def build_namespace_bridge(assemblies):
    for assembly in assemblies:
        try:
            types_ = assembly.GetExportedTypes()
        except System.Reflection.ReflectionTypeLoadException as ex:
            types_ = [t for t in ex.Types if t is not None]

        for t in types_:
            dotnet_ns = t.Namespace
            if not dotnet_ns or not dotnet_ns.startswith(DOTNET_ROOT_NS):
                continue

            # Skip compiler-generated / anonymous internal-looking names
            if t.Name.startswith("<") or "$" in t.Name:
                continue

            py_ns = dotnet_ns.replace(DOTNET_ROOT_NS, PYTHON_ROOT_NS, 1)
            py_module = _ensure_module_hierarchy(py_ns)

            clr_module = importlib.import_module(dotnet_ns)

            py_name = t.Name.split("`")[0]

            try:
                value = getattr(clr_module, py_name)
            except AttributeError:
                if DEBUG_BRIDGE:
                    print(f"[HeuristicLib] Could not bind {dotnet_ns}.{py_name}") #most unbindables are nested types that should not be accessed anyway
                continue

            setattr(py_module, py_name, value)

            current_all = set(getattr(py_module, "__all__", []))
            current_all.add(py_name)
            py_module.__all__ = sorted(current_all)

    root_module = sys.modules[PYTHON_ROOT_NS]
    prefix = PYTHON_ROOT_NS + "."
    root_children = []

    for mod_name in list(sys.modules):
        if mod_name.startswith(prefix):
            remainder = mod_name[len(prefix):]
            if "." not in remainder:
                root_children.append(remainder)

    root_module.__all__ = sorted(set(getattr(root_module, "__all__", []) + root_children))


_assemblies = load_dotnet_dlls()
build_namespace_bridge(_assemblies)

from . import InteroptUtil