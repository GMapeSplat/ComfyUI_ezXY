from .ezNodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from . import autoCastPatch
import os, shutil
import folder_paths

#install javascript extensions
module_js_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), "js")
application_root_directory = os.path.dirname(folder_paths.__file__)
application_web_extensions_directory = os.path.join(application_root_directory, "web", "extensions", "ezXY")

shutil.copytree(module_js_directory, application_web_extensions_directory, dirs_exist_ok=True)

# provide name's for custom nodes
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]