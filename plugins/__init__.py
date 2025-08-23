"""Plugin package initialization with automatic discovery.

Importing this package will automatically discover and import any
modules that define plugins. To add a new plugin, drop a ``.py`` file
into this directory that defines a subclass of
:class:`~plugins.plugin_base.Plugin`.

Examples
--------
>>> import plugins  # doctest: +SKIP
This will import all plugin modules in the directory.
"""

import importlib
import os

# Auto-discover and import all plugin modules in this package
plugins_dir = os.path.dirname(__file__)
for filename in os.listdir(plugins_dir):
    if filename.endswith(".py") and filename not in [
        "__init__.py",
        "plugin_base.py",
        "plugin_manager.py",
    ]:
        module_name = f"plugins.{filename[:-3]}"
        importlib.import_module(module_name)
