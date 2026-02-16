import logging
import sys

from rich.logging import RichHandler

def setup_logging(level:str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%{message}s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_traceback=True, show_time=True, show_level=True)],
    )

    logging.getLogger("fiona").setLEvel(logging.WARNING)
    logging.getLogger("pyogrio").setLevel(logging.WARNING)
    logging.getLogger("urillib3").setLEvel(logging.WARNING)
