from __future__ import annotations

from pathlib import Path
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore

BASE_DIR = Path(__file__).resolve().parent
FIREBASE_KEY_PATH = BASE_DIR / "firebase-key.json"

_app = None
_db = None


def get_db():
    """Initialize Firebase Admin exactly once and return the Firestore client."""
    global _app, _db

    if _db is not None:
        return _db

    if not FIREBASE_KEY_PATH.exists():
        raise FileNotFoundError(
            "firebase-key.json was not found. Replace the provided placeholder "
            "with your Firebase service-account JSON."
        )

    try:
        _app = firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate(str(FIREBASE_KEY_PATH))
        _app = firebase_admin.initialize_app(cred)

    _db = firestore.client(app=_app)
    return _db


def _json_safe(value: Any) -> Any:
    """Convert Firestore/Python values into JSON-serializable structures."""
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    return value


def _walk_collection(collection_ref, output: list[dict[str, Any]], max_documents: int = 5000):
    """Recursively walk a collection and its subcollections without hardcoded names."""
    if len(output) >= max_documents:
        return

    for document in collection_ref.stream():
        if len(output) >= max_documents:
            return

        data = _json_safe(document.to_dict() or {})
        output.append({
            "collection": collection_ref.id,
            "id": document.id,
            "path": document.reference.path,
            "data": data,
        })

        for subcollection in document.reference.collections():
            _walk_collection(subcollection, output, max_documents=max_documents)


def get_knowledge_base() -> list[dict[str, Any]]:
    """
    Discover and retrieve Firestore data dynamically.

    No collection name, document schema, or domain-specific field is assumed.
    A production deployment with a very large database should add an indexed
    retrieval layer later; this reusable template intentionally keeps the
    dependency list small and the Firestore schema fully developer-controlled.
    """
    db = get_db()
    records: list[dict[str, Any]] = []

    for collection_ref in db.collections():
        _walk_collection(collection_ref, records)

    return records
