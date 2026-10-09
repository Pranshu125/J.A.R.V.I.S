import importlib
import os
import inspect

class PluginRegistry:
    def __init__(self):
        self.plugins = {}

    def register(self, name, description, parameters=None):
        def decorator(func):
            self.plugins[name] = {
                "name": name,
                "description": description,
                "parameters": parameters or {},
                "execute": func
            }
            return func
        return decorator

    def load_plugins(self, plugin_dir="plugins"):
        if not os.path.exists(plugin_dir):
            os.makedirs(plugin_dir)
        for filename in os.listdir(plugin_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = f"{plugin_dir}.{filename[:-3]}"
                importlib.import_module(module_name)
        return self.plugins

registry = PluginRegistry()
