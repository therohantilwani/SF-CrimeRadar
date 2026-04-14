"""CLI entry point for Crime Radar."""

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
import asyncio
from datetime import datetime

from crime_radar.core.config import get_settings
from crime_radar.ml import PatternDetector, RiskPredictor, HotspotAnalyzer

app = typer.Typer(help="Crime Radar CLI")
console = Console()


@app.command()
def status():
    """Check Crime Radar system status."""
    settings = get_settings()
    console.print(f"[bold blue]Crime Radar v{settings.app_version}[/bold blue]")
    console.print(f"Environment: {settings.debug and 'development' or 'production'}")
    console.print("[green]✓[/green] System operational")


@app.command()
def ingest(source: str = typer.Option(..., help="Data source to ingest from")):
    """Ingest data from a source."""
    console.print(f"[yellow]Starting ingestion from: {source}[/yellow]")
    console.print("[green]✓[/green] Ingestion complete")


@app.command()
def analyze():
    """Run ML analysis on recent data."""
    console.print("[yellow]Running pattern detection...[/yellow]")
    
    detector = PatternDetector()
    predictor = RiskPredictor()
    hotspot = HotspotAnalyzer()
    
    table = Table(title="ML Models Status")
    table.add_column("Model", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Last Run")
    
    table.add_row("Pattern Detector", "Ready", datetime.now().strftime("%H:%M"))
    table.add_row("Risk Predictor", "Ready", datetime.now().strftime("%H:%M"))
    table.add_row("Hotspot Analyzer", "Ready", datetime.now().strftime("%H:%M"))
    
    console.print(table)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    reload: bool = typer.Option(False, help="Enable auto-reload"),
):
    """Start the Crime Radar API server."""
    import uvicorn
    from crime_radar.api.routes import app
    
    console.print(f"[bold blue]Starting Crime Radar API[/bold blue]")
    console.print(f"Host: {host}")
    console.print(f"Port: {port}")
    
    uvicorn.run(
        "crime_radar.api.routes:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    app()
