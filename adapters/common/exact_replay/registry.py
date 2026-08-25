"""Plugin registry for exact replay generators."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from adapters.common.exact_replay.pipeline import ExactReplayPlugin

_PLUGINS: dict[str, "ExactReplayPlugin"] = {}


def register_plugin(plugin: "ExactReplayPlugin") -> None:
    capability_id = plugin.capability_id
    if capability_id in _PLUGINS and _PLUGINS[capability_id] is not plugin:
        raise ValueError(f"duplicate exact-replay plugin for {capability_id}")
    _PLUGINS[capability_id] = plugin


def get_plugin(capability_id: str) -> "ExactReplayPlugin":
    # Import side-effect registration for built-in plugins.
    from adapters.common.exact_replay import plugins as _plugins  # noqa: F401

    plugin = _PLUGINS.get(capability_id)
    if plugin is None:
        raise KeyError(f"no exact-replay plugin registered for {capability_id}")
    return plugin


def list_plugins() -> list[str]:
    from adapters.common.exact_replay import plugins as _plugins  # noqa: F401

    return sorted(_PLUGINS)


def require_registered(capability_id: str) -> Callable[[], "ExactReplayPlugin"]:
    def _loader() -> "ExactReplayPlugin":
        return get_plugin(capability_id)

    return _loader
