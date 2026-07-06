bl_info = {
    "name": "Tobin's Enhanced Pie Menus",
    "author": "Tobin Cavanaugh",
    "version": (1, 0, 0),
    "blender": (5, 1, 2),
    "location": "View3D",
    "description": "Custom shading configurations and advanced camera operations from pie menus. Among several other things",
    "category": "3D View",
}

import bpy
import sys
import importlib

# Define the submodules to load
# (Ensure these match your file names exactly, minus the .py extension)
submodule_names = [
    "ShadePieMenu",
    "CameraPieMenu"
]

# Handle hot-reloading (F3 -> Reload Scripts) safely without duplicating classes
for submodule in submodule_names:
    full_module_name = f"{__name__}.{submodule}"
    if full_module_name in sys.modules:
        importlib.reload(sys.modules[full_module_name])
    else:
        importlib.import_module(f".{submodule}", package=__name__)

def register():
    # Call the register function of each individual submodule
    for submodule in submodule_names:
        module = sys.modules[f"{__name__}.{submodule}"]
        if hasattr(module, "register"):
            module.register()

def unregister():
    # Call unregister in reverse order to cleanly tear down
    for submodule in reversed(submodule_names):
        module = sys.modules[f"{__name__}.{submodule}"]
        if hasattr(module, "unregister"):
            module.unregister()

if __name__ == "__main__":
    register()