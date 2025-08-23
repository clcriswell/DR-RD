"""Base classes for the plugin architecture.

This module defines the :class:`Plugin` interface that all plugins must
implement. Plugins expose a ``name`` and ``description`` attribute and
provide a :meth:`run` method that performs the plugin's action.
"""

from __future__ import annotations


class Plugin:
    """Base class for extendable plugins in the system.

    Plugins should set a unique :attr:`name` and optionally provide a
    human-readable :attr:`description`. Subclasses must override
    :meth:`run` to implement their functionality.
    """

    def __init__(self) -> None:
        """Initialize the base plugin with empty metadata.

        Subclasses typically override this method to populate
        :attr:`name` and :attr:`description`.
        """
        self.name: str = ""
        self.description: str = ""

    def run(self, task: str, context: str):
        """Execute the plugin's action.

        Parameters
        ----------
        task:
            A short description of the work to perform.
        context:
            Additional contextual information for the plugin.

        Returns
        -------
        Any
            The result of the plugin's computation. The type depends on
            the concrete plugin implementation.

        Raises
        ------
        NotImplementedError
            If a subclass does not implement this method.

        Examples
        --------
        Creating a simple plugin that echoes the task::

            class EchoPlugin(Plugin):
                def __init__(self):
                    super().__init__()
                    self.name = "echo"

                def run(self, task: str, context: str = ""):
                    return task
        """
        raise NotImplementedError("Plugin must implement the run method.")
