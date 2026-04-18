import asyncio
import os
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from local_first_common.cli import (
    init_config_option,
    dry_run_option,
    no_llm_option,
    resolve_dry_run,
)
from local_first_common.tracking import register_tool, track_llm_run
from local_first_common.ingestion import ingest_any
from local_first_common.personas import list_personas
from local_first_common.pydantic_ai_utils import build_model, PROVIDER_DEFAULTS, VALID_PROVIDERS

from .orchestrator import run_council
from .persistence import save_council_result

TOOL_NAME = "marketing-persona-counsel"
DEFAULTS = {"provider": "ollama", "model": "llama3"}
_TOOL = register_tool("marketing-persona-counsel")

app = typer.Typer(help="Run a blog post through a council of marketing personas.")
console = Console()
err_console = Console(stderr=True)
@app.command()
def main(
    source: Optional[str] = typer.Argument(
        None,
        help="URL or local path to a blog post markdown file.",
    ),
    provider: str = typer.Option(
        os.environ.get("MODEL_PROVIDER", "ollama"),
        "--provider",
        "-p",
        help=f"LLM provider. Choices: {', '.join(VALID_PROVIDERS)}",
    ),
    model: Optional[str] = typer.Option(
        None, "--model", "-m", help="Override the provider's default model."
    ),
    vault: Optional[Path] = typer.Option(
        None, "--vault", help="Override the Obsidian vault path."
    ),
    dry_run: Annotated[bool, dry_run_option()] = False,
    no_llm: Annotated[bool, no_llm_option()] = False,
    concurrency: int = typer.Option(
        3, "--concurrency", "-c", help="Max parallel API calls."
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    list_personas_flag: bool = typer.Option(
        False, "--list-personas", help="List available marketing personas."
    ),
    init_config: Annotated[bool, init_config_option(TOOL_NAME, DEFAULTS)] = False,
) -> None:
    """Evaluate a blog post using marketing persona agents."""

    # Handle --list-personas
    if list_personas_flag:
        personas = list_personas("Brand", vault_path=vault)
        if not personas:
            err_console.print("[yellow]No marketing personas found. Check OBSIDIAN_VAULT_PATH/personas/Brand[/yellow]")
            raise typer.Exit(1)
        console.print("\n[bold]Available Marketing Personas:[/bold]\n")
        for p in personas:
            console.print(f"  [cyan]{p.name}[/cyan] ({p.archetype})")
        console.print()
        raise typer.Exit()

    # 3. Resolve Model
    actual_provider = "mock" if no_llm else provider

    if source is None:
        err_console.print("[red]Error:[/red] Missing argument 'SOURCE'.")
        raise typer.Exit(1)

    dry_run = resolve_dry_run(dry_run, no_llm)
    
    # 1. Load Personas
    personas = list_personas("Brand", vault_path=vault)
    if not personas:
        err_console.print("[red]Error:[/red] No marketing personas found in OBSIDIAN_VAULT_PATH/personas/Brand")
        raise typer.Exit(1)
        
    if verbose:
        console.print(f"[dim]Loaded {len(personas)} personas: {', '.join(p.name for p in personas)}[/dim]")

    # 2. Ingest Content
    try:
        title, content = ingest_any(source, tool=_TOOL)
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
    with track_llm_run("marketing-persona-counsel", f"{provider}:{model_name}", source_location=source) as run:
        result = asyncio.run(run_council(
            personas, content, title, source, pai_model, concurrency
        ))
        run.track(result, item_count=len(personas))

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
