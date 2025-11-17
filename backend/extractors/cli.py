"""
Command Line Interface for iMessage Extraction
Forensic extraction tool with comprehensive options
"""

import logging
import sys
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from backend.extractors.imessage_extractor import iMessageExtractor
from backend.config import validate_environment, IMESSAGE_DB_PATH

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

console = Console()


@click.group()
def cli():
    """iExporter3 - Forensic-Grade iMessage Extraction Tool"""
    pass


@cli.command()
def check():
    """Check system environment and prerequisites."""
    console.print("\n[bold]iExporter3 Environment Check[/bold]\n")

    validations = validate_environment()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Check", style="dim")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    for check, passed in validations.items():
        status = "[green]✓ PASS[/green]" if passed else "[red]✗ FAIL[/red]"
        details = ""

        if check == "python_version":
            import sys
            details = f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        elif check == "imessage_db_exists":
            details = str(IMESSAGE_DB_PATH) if passed else "Not found"
        elif check == "imessage_db_readable":
            details = "Can read" if passed else "Permission denied"

        table.add_row(check.replace("_", " ").title(), status, details)

    console.print(table)

    if not validations["imessage_db_exists"]:
        console.print(
            "\n[yellow]⚠️  iMessage database not found.[/yellow]"
        )
        console.print(
            "Expected location: ~/Library/Messages/chat.db\n"
            "This is normal on non-macOS systems.\n"
        )

    if not validations["imessage_db_readable"]:
        console.print(
            "\n[yellow]⚠️  Cannot read iMessage database.[/yellow]"
        )
        console.print(
            "You may need to grant Full Disk Access:\n"
            "1. Open System Preferences > Security & Privacy > Privacy\n"
            "2. Select 'Full Disk Access'\n"
            "3. Add Terminal.app or your terminal emulator\n"
        )

    overall_pass = all(validations.values())
    if overall_pass:
        console.print("\n[green]✓ All checks passed! Ready for extraction.[/green]\n")
    else:
        console.print(
            "\n[red]✗ Some checks failed. Review issues above.[/red]\n"
        )


@cli.command()
@click.argument("case_id")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output database path (auto-generated if not specified)",
)
@click.option(
    "--source",
    "-s",
    type=click.Path(exists=True),
    help="Custom source database path (default: macOS iMessage DB)",
)
@click.option(
    "--user",
    "-u",
    default="system",
    help="User performing extraction (for audit trail)",
)
def extract(
    case_id: str,
    output: Optional[str],
    source: Optional[str],
    user: str,
):
    """
    Extract messages from iMessage database.

    CASE_ID: Unique identifier for this case (e.g., ABC2024)
    """
    console.print(
        Panel.fit(
            f"[bold]iExporter3 Forensic Extraction[/bold]\n\n"
            f"Case ID: {case_id}\n"
            f"User: {user}",
            border_style="cyan",
        )
    )

    # Create extractor
    extractor = iMessageExtractor(
        case_id=case_id,
        output_db_path=output,
        user=user,
        source_db_path=Path(source) if source else None,
    )

    # Validate source
    console.print("\n[bold]Validating source database...[/bold]")
    if not extractor.validate_source():
        console.print("[red]✗ Source validation failed![/red]")
        console.print(f"Source path: {extractor.get_source_db_path()}")
        sys.exit(1)

    console.print(f"[green]✓ Source validated: {extractor.get_source_db_path()}[/green]")

    # Start extraction
    console.print("\n[bold]Starting extraction...[/bold]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Extracting messages and attachments...", total=None)

        # Run extraction
        result = extractor.extract()

        progress.update(task, completed=True)

    # Display results
    console.print("\n[bold]Extraction Results[/bold]\n")

    if result["success"]:
        stats = result["stats"]

        table = Table(show_header=False)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="green")

        table.add_row("Messages Extracted", f"{stats['total_messages']:,}")
        table.add_row("Attachments Extracted", f"{stats['total_attachments']:,}")
        table.add_row("Conversations", f"{stats['total_conversations']:,}")
        table.add_row("Duration", f"{stats['duration_seconds']:.2f} seconds")
        table.add_row("Output Database", result["output_db_path"])
        table.add_row("Source Hash", result["source_db_hash"][:16] + "...")

        console.print(table)
        console.print("\n[green]✓ Extraction completed successfully![/green]\n")

    else:
        console.print(f"[red]✗ Extraction failed: {result.get('error')}[/red]\n")
        sys.exit(1)


@cli.command()
@click.argument("database_path", type=click.Path(exists=True))
def info(database_path: str):
    """Display information about an extracted database."""
    from backend.models import get_session, ExtractionMetadata, Message, Attachment

    console.print(
        Panel.fit(
            f"[bold]Database Information[/bold]\n\n{database_path}",
            border_style="cyan",
        )
    )

    session = get_session(database_path)

    # Get extraction metadata
    metadata = session.query(ExtractionMetadata).first()

    if not metadata:
        console.print("[red]No extraction metadata found in database.[/red]")
        session.close()
        return

    # Display metadata
    console.print("\n[bold]Extraction Metadata[/bold]\n")

    table = Table(show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    table.add_row("Case ID", metadata.case_id)
    table.add_row(
        "Extraction Time", metadata.get_extraction_datetime().strftime("%Y-%m-%d %H:%M:%S UTC")
    )
    table.add_row("Extractor", metadata.extractor_name)
    table.add_row("Tool Version", metadata.extractor_version or "Unknown")
    table.add_row("Source Database", metadata.source_db_path)
    table.add_row("Source Hash", metadata.source_db_hash)
    table.add_row("Messages", f"{metadata.total_messages:,}")
    table.add_row("Attachments", f"{metadata.total_attachments:,}")
    table.add_row("Conversations", f"{metadata.total_conversations:,}")

    console.print(table)

    # Get current counts
    message_count = session.query(Message).count()
    attachment_count = session.query(Attachment).count()

    console.print(f"\n[bold]Current Database Contents[/bold]\n")
    console.print(f"Messages: {message_count:,}")
    console.print(f"Attachments: {attachment_count:,}")

    session.close()


if __name__ == "__main__":
    cli()
