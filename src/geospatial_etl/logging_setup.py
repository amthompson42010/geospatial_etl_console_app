import logging
from rich.logging import RichHandler


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_time=True, show_level=True)],
    )

    # Reduce noisy libs
    logging.getLogger("fiona").setLevel(logging.WARNING)
    logging.getLogger("pyogrio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
