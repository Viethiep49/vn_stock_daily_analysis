import json
import logging
import os
from datetime import datetime
from src.agents.protocols import StageResult

logger = logging.getLogger(__name__)

# Write to logs/ subdir instead of project root
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
LOGS_DIR = os.path.join(_ROOT, "logs")
TELEMETRY_FILE = os.path.join(LOGS_DIR, "telemetry.jsonl")


def log_stage_result(result: StageResult):
    """Log an agent stage result to logs/telemetry.jsonl."""
    try:
        os.makedirs(LOGS_DIR, exist_ok=True)

        if hasattr(result, "model_dump"):
            data = result.model_dump()
        else:
            data = result.dict()

        data["timestamp"] = datetime.utcnow().isoformat()

        with open(TELEMETRY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, default=str) + "\n")

        logger.info(f"Telemetry logged for agent: {result.agent_name}")
    except Exception as e:
        logger.error(f"Failed to log telemetry: {e}")
