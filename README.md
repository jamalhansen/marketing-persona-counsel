# Marketing Persona Counsel

Tool #24 in the `local-ai-tools` series. Analyzes marketing copy, landing pages, or product ideas from the perspective of a specific customer persona.

## What It Does

Takes a URL or markdown file and runs it through an agentic persona (defined in your Obsidian vault) to get structured feedback on how well it resonates with that target audience.

## Installation

```bash
uv sync
```

## Usage

The tool is available as `marketing-persona-counsel` after `uv sync`.

```bash
uv run marketing-persona-counsel --url https://example.com/landing-page --persona "Founder"
```

Standard flags supported: `--dry-run`, `--no-llm`, `--provider`, `--model`.

## Project Structure

```
marketing-persona-counsel/
├── src/marketing_persona_counsel/
│   ├── logic.py         # Core agent logic
│   ├── models.py        # SQLModel and Pydantic models
│   ├── ingestion.py     # Content ingestion from URLs/files
│   └── ...
├── pyproject.toml
└── README.md
```
