from __future__ import annotations

import json
import typer

from .config import Settings
from .etl import run_pipeline
from .logging_setup import setup_logging

app = typer.Typer(add_completion=False)


@app.command()
def main(
    log_level: str = typer.Option("INFO", help="DEBUG|INFO|WARNING|ERROR"),
):
    """
    Run the geospatial ETL pipeline using env/.env configuration.
    """
    setup_logging(log_level)
    settings = Settings()
    meta = run_pipeline(settings)
    typer.echo(json.dumps(meta, indent=2))


if __name__ == "__main__":
    app()
