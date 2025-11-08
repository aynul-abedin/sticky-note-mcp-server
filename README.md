# AI Sticky Notes MCP Server

This demo shows a richer [Model Context Protocol](https://github.com/modelcontextprotocol) server built with `FastMCP`. It turns a simple sticky-note list into a structured note system with tagging, pinning, archiving, and summarisation helpers.

## Features
- Structured storage with automatic migration from the legacy `notes.txt` file.
- Tools for creating, listing, searching, updating, deleting, and bulk-clearing notes.
- Optional tagging, pinned state, and archived flag for each note.
- Resources that expose the latest note, pinned notes, and aggregate stats.
- Prompt templates for summarising notes or producing a roadmap for a specific tag.

## What You Can Do With This MCP Server

This server lets you:
- **Create notes** with tags and pinned status for important items
- **List and filter** notes by tags, pinned status, or archived state
- **Search** through note content and tags to find specific information
- **Update** existing notes to change their content, tags, or status
- **Delete** individual notes or bulk-clear all/archived notes
- **Pin** important notes so they stand out in summaries
- **Archive** completed or outdated notes without losing them
- **Generate summaries** of your active notes using AI prompts
- **Create roadmaps** from tagged notes to plan projects or tasks
- **Access stats** showing total, active, archived, and pinned note counts
- **Retrieve** the latest note or all pinned notes via resources

## Available MCP Interfaces

### Tools
- `add_note(message, tags=None, pinned=False)` – Create a new note with optional tags (comma-separated) and pinned flag
- `read_notes(include_archived=False)` – Get all notes sorted by creation date (newest first)
- `list_notes(limit=20, offset=0, tag=None, pinned_only=False, include_archived=False)` – Paginated note listing with filtering
- `search_notes(query, include_archived=False)` – Find notes containing the query text in message or tags
- `update_note(note_id, message=None, tags=None, pinned=None, archived=None)` – Modify an existing note's content or metadata
- `delete_note(note_id)` – Permanently remove a specific note
- `clear_notes(archived_only=False)` – Delete all notes, or just archived ones

Each tool returns structured JSON so calling clients can display note metadata alongside the original message.

### Resources
- `notes://latest` – most recent active note text.
- `notes://pinned` – newline-delimited pinned notes with identifiers.
- `notes://stats` – counts for total, active, archived, and pinned notes.

### Prompts
- `note_summary_prompt()` – Asks the AI to summarize all active notes and highlights any pinned ones
- `note_roadmap_prompt(target_tag=None)` – Asks the AI to turn matching notes into a prioritized roadmap (optionally filtered by tag)

## Example Use Cases

1. **Personal Task Management**: Pin urgent tasks, tag by project, archive completed items
2. **Brainstorming**: Quickly capture ideas with tags, then use the roadmap prompt to organize them
3. **Meeting Notes**: Store discussion points with meeting tags, search later by keywords
4. **Learning Tracker**: Save learning resources or tips, organize by topic tags
5. **Project Planning**: Create notes for features or bugs, filter by tag, generate roadmaps
6. **Daily Journaling**: Quick thoughts throughout the day, summarize with AI at day's end

## Running the Server

Activate your environment and launch the MCP server CLI:

```powershell
uv run mcp dev ./main.py
```

From another MCP-compatible client, point to the generated manifest or directly invoke the tools/resources/prompts exposed by this server.

