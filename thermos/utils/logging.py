import logging
import sys

def setup_logging(level: int = logging.INFO) -> None:
    """Configures the root logger."""
    
    logging.basicConfig(
        level=level,
        format="[%(module)s] %(asctime)s %(levelname)s %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )

def get_logger(name: str) -> logging.Logger:
    """Returns a logger for the given name."""
    return logging.getLogger(name)
