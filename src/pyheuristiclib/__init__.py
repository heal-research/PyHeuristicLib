import os
import sys
import types
import importlib.resources as pkg_resources
from pathlib import Path
from collections import defaultdict

from pythonnet import load
load("coreclr")

import clr
import System

from . import InteroptUtil


DOTNET_ROOT_NS = "HEAL.HeuristicLib"
PYTHON_ROOT_NS = __name__


def load_dotnet_dll():
    dll_name = "HEAL.HeuristicLib.Core.dll"

    pkg = pkg_resources.files("pyheuristiclib.heuristiclib")
    dll_path = Path(str(pkg.joinpath(dll_name)))

    # Let .NET find dependent DLLs
    dll_dir = str(dll_path.parent)
    if dll_dir not in sys.path:
        sys.path.insert(0, dll_dir)

    os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")

    # Load main assembly
    System.Reflection.Assembly.LoadFrom(str(dll_path))
    clr.AddReference(dll_name.removesuffix(".dll"))
    print(f"[HeuristicLib] .NET DLL loaded from: {dll_path}")

    return System.Reflection.Assembly.Load(dll_name.removesuffix(".dll"))


def _ensure_module(module_name: str):
    """Create or return a Python module registered in sys.modules."""
    module = sys.modules.get(module_name)
    if module is None:
        module = types.ModuleType(module_name)
        module.__package__ = module_name
        sys.modules[module_name] = module
    return module


def _ensure_module_hierarchy(module_name: str):
    """
    Ensure all parent modules exist and are linked as attributes.
    Example:
      pyheuristiclib.Algorithms.Evolutionary
    creates/links:
      pyheuristiclib
      pyheuristiclib.Algorithms
      pyheuristiclib.Algorithms.Evolutionary
    """
    parts = module_name.split(".")
    for i in range(1, len(parts) + 1):
        current_name = ".".join(parts[:i])
        current_mod = _ensure_module(current_name)

        if i > 1:
            parent_name = ".".join(parts[:i - 1])
            parent_mod = _ensure_module(parent_name)
            setattr(parent_mod, parts[i - 1], current_mod)

    return sys.modules[module_name]


def _safe_python_name(type_name: str) -> str:
    """
    Convert .NET type names into safer Python attribute names.
    Handles nested classes and generic arity markers.
    Examples:
      Outer+Inner -> Outer_Inner
      Foo`1 -> Foo
    """
    name = type_name.replace("+", "_")
    if "`" in name:
        name = name.split("`", 1)[0]
    return name


def build_namespace_bridge(assembly):
    """
    Dynamically map .NET namespaces under HEAL.HeuristicLib.*
    to Python modules under pyheuristiclib.*.
    """
    ns_map = defaultdict(list)

    try:
        exported_types = assembly.GetExportedTypes()
    except System.Reflection.ReflectionTypeLoadException as ex:
        # Fallback: use whatever types could be loaded
        exported_types = [t for t in ex.Types if t is not None]

    for t in exported_types:
        ns = t.Namespace
        if not ns or not ns.startswith(DOTNET_ROOT_NS):
            continue
        ns_map[ns].append(t)

    # Ensure all namespace modules exist first
    for dotnet_ns in ns_map:
        py_ns = dotnet_ns.replace(DOTNET_ROOT_NS, PYTHON_ROOT_NS, 1)
        _ensure_module_hierarchy(py_ns)

    # Attach reflected types to their mapped Python modules
    for dotnet_ns, type_list in ns_map.items():
        py_ns = dotnet_ns.replace(DOTNET_ROOT_NS, PYTHON_ROOT_NS, 1)
        module = sys.modules[py_ns]

        exported_names = []

        for t in type_list:
            py_type_name = _safe_python_name(t.Name)

            # Avoid overwriting an existing attribute unless it is identical
            existing = getattr(module, py_type_name, None)
            if existing is None:
                setattr(module, py_type_name, t)
            elif existing is not t:
                # Rare collision case; keep both by storing full name alias
                full_alias = _safe_python_name(t.FullName.split(".")[-1])
                setattr(module, full_alias, t)
                py_type_name = full_alias

            exported_names.append(py_type_name)

        # Helps dir() a bit
        existing_all = getattr(module, "__all__", [])
        module.__all__ = sorted(set(existing_all + exported_names))

    # Optional: expose discovered submodules on the package root
    root_module = sys.modules[PYTHON_ROOT_NS]
    root_children = []

    prefix = PYTHON_ROOT_NS + "."
    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith(prefix):
            remainder = mod_name[len(prefix):]
            if "." not in remainder:
                root_children.append(remainder)

    existing_root_all = getattr(root_module, "__all__", [])
    root_module.__all__ = sorted(set(existing_root_all + root_children))


_assembly = load_dotnet_dll()
build_namespace_bridge(_assembly)