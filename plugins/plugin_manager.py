"""Utilities for discovering and invoking plugins.

The :class:`PluginManager` class scans the :mod:`plugins` package for
subclasses of :class:`~plugins.plugin_base.Plugin` and provides a simple
interface for running them by name.
"""

from __future__ import annotations

import importlib
import inspect
import os

from plugins.plugin_base import Plugin


class PluginManager:
    """Manages discovery and execution of plugins.

    Examples
    --------
    >>> pm = PluginManager()
    >>> sorted(pm.plugins)  # doctest: +SKIP
    ['eco_impact']
    """

    def __init__(self) -> None:
        """Discover and register available plugins.

        On instantiation, the manager imports all modules in the
        ``plugins`` directory and registers any subclasses of
        :class:`Plugin` using their declared ``name`` attribute.
        """
        # Automatically register all plugins in the plugins directory
        self.plugins = {}
        plugins_dir = os.path.dirname(__file__)
        for filename in os.listdir(plugins_dir):
            if filename.endswith(".py") and filename not in [
                "__init__.py",
                "plugin_base.py",
                "plugin_manager.py",
            ]:
                module_name = f"plugins.{filename[:-3]}"
                module = importlib.import_module(module_name)
                # Find Plugin subclasses in the module
                for name, cls in inspect.getmembers(module, inspect.isclass):
                    if issubclass(cls, Plugin) and cls is not Plugin:
                        instance = cls()
                        # Register plugin by its name
                        if instance.name:
                            self.plugins[instance.name] = instance

    def run_plugin(self, name: str, task: str, context: str = ""):
        """Run the specified plugin by name.

        Parameters
        ----------
        name:
            The registered name of the plugin to execute.
        task:
            Description of the work to pass to the plugin.
        context:
            Additional context for the plugin, if any.

        Returns
        -------
        Any
            The value returned by the plugin's :meth:`run` method.

        Raises
        ------
        ValueError
            If the requested plugin is not found.

        Examples
        --------
        >>> pm = PluginManager()
        >>> pm.run_plugin("eco_impact", "Build a cloud service")  # doctest: +SKIP
        {'Energy Usage': '200 kWh/year', ...}
        """
        if name not in self.plugins:
            raise ValueError(f"Plugin '{name}' not found.")
        # Log plugin invocation and increment call count
        import streamlit as st

        st.session_state["plugin_calls"] = st.session_state.get("plugin_calls", 0) + 1
        plugin = self.plugins[name]
        return plugin.run(task, context)
