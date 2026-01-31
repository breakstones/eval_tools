"""Debug logging utility for evaluator testing."""
import logging
from datetime import datetime

# Setup file logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('evaluator_debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def debug_log(message: str):
    """Log a debug message with timestamp."""
    logger.debug(f"[DEBUG] {message}")
    print(f"[DEBUG] {message}", flush=True)
