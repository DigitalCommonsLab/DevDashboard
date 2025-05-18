import json
import logging
from datetime import datetime

logger = logging.getLogger("devdashboard")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def log_event(message: str, **fields: str) -> None:
    entry = {"timestamp": datetime.utcnow().isoformat(), "message": message}
    entry.update(fields)
    logger.info(json.dumps(entry))
