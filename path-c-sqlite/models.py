"""Foundry Local model loading, shared by the ingest script and the app.

Kept in one place so that ingestion and querying are guaranteed to use the same
embedding model. Vectors from two different embedding models are not comparable,
and mixing them produces meaningless similarity scores rather than an error.
"""

from __future__ import annotations

from foundry_local_sdk import Configuration, FoundryLocalManager

import config

_initialised = False


def _manager():
    """Initialise the SDK once per process and return the manager."""
    global _initialised
    if not _initialised:
        FoundryLocalManager.initialize(Configuration(app_name=config.APP_NAME))
        _initialised = True
    return FoundryLocalManager.instance


def _prepare(alias: str, label: str, on_progress=None):
    """Fetch a model from the catalog, download it if needed, and load it."""
    model = _manager().catalog.get_model(alias)

    if on_progress is None:
        def on_progress(pct):
            print(f"\rDownloading {label} model: {pct:.1f}%", end="", flush=True)

    model.download(on_progress)
    model.load()
    return model


def load_embedding_model(on_progress=None):
    return _prepare(config.EMBEDDING_MODEL, "embedding", on_progress)


def load_chat_model(on_progress=None):
    return _prepare(config.CHAT_MODEL, "chat", on_progress)
