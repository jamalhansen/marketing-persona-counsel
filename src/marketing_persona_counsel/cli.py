import asyncio
import os
from pathlib import Path
from typing import Annotated, Optional

import typer
from local_first_common.cli import (
    dry_run_option,
    no_llm_option,
    resolve_dry_run,
)
from local_first_common.tracking import register_tool, timed_run
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from local_first_common.pydantic_ai_utils import build_model, PROVIDER_DEFAULTS, VALID_PROVIDERS
from local_first_common.personas import list_obsidian_personas
from .ingestion import fetch_url_content, load_markdown_content
from .orchestrator import run_council
from .persistence import save_council_result

_TOOL = register_tool("marketing-persona-counsel")
app = typer.Typer(help="Run a blog post through a council of marketing personas.")
console = Console()
err_console = Console(stderr=True)


@app.command()
def main(
    source: Annotated[
        Optional[str],
        typer.Argument(help="URL or local path to a blog post markdown file."),
    ] = None,
    provider: Annotated[
        str,
        typer.Option(
            "--provider",
            "-p",
            help=f"LLM provider. Choices: {', '.join(VALID_PROVIDERS)}",
        ),
    ] = os.environ.get("MODEL_PROVIDER", "ollama"),
    model: Annotated[
        Optional[str],
        typer.Option("--model", "-m", help="Override the provider's default model."),
    ] = None,
    dry_run: bool = dry_run_option(),
    no_llm: bool = no_llm_option(),
    concurrency: Annotated[
        int,
        typer.Option("--concurrency", "-c", help="Max parallel API calls."),
    ] = 3,
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    list_personas: bool = typer.Option(False, "--list-personas", help="List available marketing personas."),
) -> None:
    """Evaluate a blog post using marketing persona agents."""
    
    # Handle --list-personas
    if list_personas:
        personas = list_obsidian_personas()
        if not personas:
            err_console.print("[yellow]No marketing personas found. Check OBSIDIAN_VAULT_PATH/personas/brand[/yellow]")
            raise typer.Exit(1)
        console.print("\n[bold]Available Marketing Personas:[/bold]\n")
        for p in personas:
            console.print(f"  [cyan]{p.name}[/cyan] ({p.archetype})")
        console.print()
        raise typer.Exit()

    if source is None:
        err_console.print("[red]Error:[/red] Missing argument 'SOURCE'.")
        raise typer.Exit(1)

    dry_run = resolve_dry_run(dry_run, no_llm)
    
    # 1. Load Personas
    personas = list_obsidian_personas()
    if not personas:
        err_console.print("[red]Error:[/red] No marketing personas found in OBSIDIAN_VAULT_PATH/personas/brand")
        raise typer.Exit(1)
        
    if verbose:
        console.print(f"[dim]Loaded {len(personas)} personas: {', '.join(p.name for p in personas)}[/dim]")

    # 2. Ingest Content
    try:
        if source.startswith("http"):
            title, content = fetch_url_content(source)
        else:
            path = Path(source)
            if not path.exists():
                err_console.print(f"[red]Error:[/red] File not found: {source}")
                raise typer.Exit(1)
            title, content = load_markdown_content(path)
    except Exception as e:
        err_console.print(f"[red]Failed to ingest content:[/red] {e}")
        raise typer.Exit(1)

    console.print(f"[bold]Evaluating:[/bold] [cyan]{title}[/cyan]")
    
    # 3. Resolve Model
    actual_provider = "mock" if no_llm else provider
    actual_model = "test-model" if no_llm else model
    
    try:
        pai_model = build_model(actual_provider, actual_model)
    except Exception as e:
        err_console.print(f"[red]Error building model:[/red] {e}")
        raise typer.Exit(1)

    model_name = actual_model or PROVIDER_DEFAULTS.get(actual_provider, "unknown")

    # 4. Run Council
    with timed_run("marketing-persona-counsel", f"{provider}:{model_name}", source_location=source) as _run:
        result = asyncio.run(run_council(
            personas, content, title, source, pai_model, concurrency
        ))
        _run.item_count = len(personas)

    # 5. Display Results
    table = Table(title=f"Council Evaluation: {title}")
    table.add_column("Persona", style="cyan")
    table.add_column("Sentiment", style="magenta")
    table.add_column("Interest", justify="right")
    table.add_column("Engage", justify="right")
    table.add_column("Friend", justify="right")
    table.add_column("Share", justify="right")
    
    for e in result.evaluations:
        table.add_row(
            e.persona_name,
            e.sentiment,
            str(e.interest_score),
            str(e.engagement_score),
            str(e.friendliness_score),
            str(e.shareability_score)
        )
        
    console.print(table)
    
    console.print(f"\n[bold]Averages:[/bold] Interest: {result.average_interest:.1f} | Engagement: {result.average_engagement:.1f}")
    
    for e in result.evaluations:
        with console.status(f"Tips from {e.persona_name}..."):
            console.print(Panel(
                "[bold]Outstanding Questions:[/bold]\n- " + "\n- ".join(e.outstanding_questions) + 
                "\n\n[bold]Tips to Improve:[/bold]\n- " + "\n- ".join(e.tips_to_improve) +
                f"\n\n[italic]\"{e.narrative}\"[/italic]",
                title=f"Feedback: {e.persona_name}",
                expand=False
            ))

    # 6. Persistence
    if not dry_run:
        save_council_result(result)
        console.print("\n[green]Results saved to SQLite history.[/green]")
    else:
        console.print("\n[yellow][dry-run] Results not saved.[/yellow]")


if __name__ == "__main__":
    app()
