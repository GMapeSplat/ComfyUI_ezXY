import os, shutil
import folder_paths


# Bring in config
import yaml
config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.yaml")
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)


# Provide name's for custom nodes
from .ezNodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]


# Use backend patches
if config['auto_typecast']:
    from . import autoCastPatch


# Install javascript extensions
module_js_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), "js")
application_root_directory = os.path.dirname(folder_paths.__file__)
application_web_extensions_directory = os.path.join(application_root_directory, "web", "extensions", "ezXY")

if config['force_numbertype_compatability']:
    shutil.copytree(module_js_directory, application_web_extensions_directory, dirs_exist_ok=True)
    
elif os.path.exists(application_web_extensions_directory):
    shutil.rmtree(application_web_extensions_directory)
    print('ezXY extensions removed')