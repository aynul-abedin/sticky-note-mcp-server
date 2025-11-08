import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AI Sticky Notes")

BASE_DIR = Path(__file__).resolve().parent
LEGACY_NOTES_FILE = BASE_DIR / "notes.txt"
NOTES_FILE = BASE_DIR / "notes.json"

Note = Dict[str, object]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_tags(raw_tags: Optional[str]) -> List[str]:
    if not raw_tags:
        return []
    tags = {tag.strip().lower() for tag in raw_tags.split(",") if tag.strip()}
    return sorted(tags)


def ensure_storage() -> None:
    if NOTES_FILE.exists():
        return

    notes: List[Note] = []
    if LEGACY_NOTES_FILE.exists():
        with LEGACY_NOTES_FILE.open("r", encoding="utf-8") as legacy:
            for line in legacy:
                content = line.strip()
                if content:
                    notes.append(
                        {
                            "id": uuid.uuid4().hex,
                            "message": content,
                            "created_at": _now(),
                            "tags": [],
                            "pinned": False,
                            "archived": False,
                        }
                    )

    save_notes(notes)


def load_notes() -> List[Note]:
    ensure_storage()
    with NOTES_FILE.open("r", encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError:
            data = []
    return data if isinstance(data, list) else []


def save_notes(notes: List[Note]) -> None:
    with NOTES_FILE.open("w", encoding="utf-8") as handle:
        json.dump(notes, handle, indent=2, ensure_ascii=True)


def _find_note(notes: List[Note], note_id: str) -> Optional[Note]:
    for note in notes:
        if note.get("id") == note_id:
            return note
    return None


def _visible_notes(notes: List[Note], include_archived: bool = False) -> List[Note]:
    if include_archived:
        return list(notes)
    return [note for note in notes if not note.get("archived", False)]


@mcp.tool()
def add_note(message: str, tags: Optional[str] = None, pinned: bool = False) -> Note:
    """Create a new note with optional tags and pinned state."""

    payload = message.strip()
    if not payload:
        raise ValueError("Note message cannot be empty.")

    notes = load_notes()
    note = {
        "id": uuid.uuid4().hex,
        "message": payload,
        "created_at": _now(),
        "tags": _parse_tags(tags),
        "pinned": bool(pinned),
        "archived": False,
    }
    notes.append(note)
    save_notes(notes)
    return note


@mcp.tool()
def read_notes(include_archived: bool = False) -> List[Note]:
    """Return all notes, optionally including archived entries."""

    notes = load_notes()
    active = _visible_notes(notes, include_archived=include_archived)
    return sorted(active, key=lambda n: n.get("created_at", ""), reverse=True)


@mcp.tool()
def list_notes(
    limit: int = 20,
    offset: int = 0,
    tag: Optional[str] = None,
    pinned_only: bool = False,
    include_archived: bool = False,
) -> List[Note]:
    """List notes with simple pagination and filtering."""

    notes = _visible_notes(load_notes(), include_archived=include_archived)
    if tag:
        tag_lower = tag.strip().lower()
        notes = [note for note in notes if tag_lower in note.get("tags", [])]
    if pinned_only:
        notes = [note for note in notes if note.get("pinned")]

    notes = sorted(notes, key=lambda n: n.get("created_at", ""), reverse=True)
    return notes[offset : offset + max(limit, 0)]


@mcp.tool()
def search_notes(query: str, include_archived: bool = False) -> List[Note]:
    """Find notes whose text or tags contain the query string."""

    needle = query.strip().lower()
    if not needle:
        raise ValueError("Query must not be empty.")

    notes = _visible_notes(load_notes(), include_archived=include_archived)
    results = []
    for note in notes:
        if needle in str(note.get("message", "")).lower():
            results.append(note)
            continue
        if any(needle in tag for tag in note.get("tags", [])):
            results.append(note)
    return sorted(results, key=lambda n: n.get("created_at", ""), reverse=True)


@mcp.tool()
def update_note(
    note_id: str,
    message: Optional[str] = None,
    tags: Optional[str] = None,
    pinned: Optional[bool] = None,
    archived: Optional[bool] = None,
) -> Note:
    """Edit an existing note's content or metadata."""

    notes = load_notes()
    note = _find_note(notes, note_id)
    if not note:
        raise ValueError("Note not found.")

    if message is not None:
        payload = message.strip()
        if not payload:
            raise ValueError("Updated message cannot be empty.")
        note["message"] = payload
    if tags is not None:
        note["tags"] = _parse_tags(tags)
    if pinned is not None:
        note["pinned"] = bool(pinned)
    if archived is not None:
        note["archived"] = bool(archived)

    save_notes(notes)
    return note


@mcp.tool()
def delete_note(note_id: str) -> str:
    """Remove a note permanently."""

    notes = load_notes()
    remaining = [note for note in notes if note.get("id") != note_id]
    if len(remaining) == len(notes):
        raise ValueError("Note not found.")

    save_notes(remaining)
    return "Note deleted."


@mcp.tool()
def clear_notes(archived_only: bool = False) -> str:
    """Delete all notes or only archived ones."""

    notes = load_notes()
    if archived_only:
        notes = [note for note in notes if not note.get("archived", False)]
        save_notes(notes)
        return "Archived notes cleared."

    save_notes([])
    return "All notes cleared."


@mcp.resource("notes://latest")
def get_latest_note() -> str:
    """Return the most recent non-archived note."""

    notes = _visible_notes(load_notes())
    if not notes:
        return "No notes yet."

    latest = max(notes, key=lambda n: n.get("created_at", ""))
    return latest.get("message", "")


@mcp.resource("notes://pinned")
def get_pinned_notes() -> str:
    """Return pinned notes as a newline-delimited string."""

    notes = [note for note in _visible_notes(load_notes()) if note.get("pinned")]
    if not notes:
        return "No pinned notes."

    lines = [f"[{note.get('id')}] {note.get('message')}" for note in notes]
    return "\n".join(lines)


@mcp.resource("notes://stats")
def get_note_stats() -> Dict[str, int]:
    """Return simple counts for notes."""

    notes = load_notes()
    active = _visible_notes(notes)
    return {
        "total": len(notes),
        "active": len(active),
        "archived": len(notes) - len(active),
        "pinned": sum(1 for note in active if note.get("pinned")),
    }


@mcp.prompt()
def note_summary_prompt() -> str:
    """Prompt asking for a high-level summary of active notes."""

    notes = _visible_notes(load_notes())
    if not notes:
        return "There are no notes yet."

    pinned = [note for note in notes if note.get("pinned")]
    pinned_text = " | Pinned: " + "; ".join(note.get("message", "") for note in pinned) if pinned else ""

    joined = "; ".join(note.get("message", "") for note in notes)
    return f"Summarize the current notes: {joined}{pinned_text}"


@mcp.prompt()
def note_roadmap_prompt(target_tag: Optional[str] = None) -> str:
    """Prompt for converting notes into an actionable roadmap."""

    notes = _visible_notes(load_notes())
    if target_tag:
        tag_lower = target_tag.strip().lower()
        notes = [note for note in notes if tag_lower in note.get("tags", [])]

    if not notes:
        return "There are no matching notes yet."

    lines = []
    for note in notes:
        tags = ",".join(note.get("tags", []))
        tags_part = f" (tags: {tags})" if tags else ""
        lines.append(f"- {note.get('message')}{tags_part}")

    header = (
        "Help create a prioritized roadmap from these notes:"
        if not target_tag
        else f"Help organize the '{target_tag}' notes into a roadmap:"
    )
    return f"{header}\n" + "\n".join(lines)
