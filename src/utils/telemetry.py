import json
import logging
from datetime import datetime
from src.agents.protocols import StageResult

logger = logging.getLogger(__name__)

TELEMETRY_FILE = "telemetry.jsonl"

def log_stage_result(result: StageResult):
    """Log an agent stage result to a JSONL file."""
    try:
        # Convert to dict, handling enums and nested models
        # Using model_dump() for Pydantic V2 compatibility if present
        if hasattr(result, "model_dump"):
            data = result.model_dump()
        else:
            data = result.dict()
            
        data["timestamp"] = datetime.utcnow().isoformat()
        
        # Ensure directory exists if needed (though here it's root)
        with open(TELEMETRY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, default=str) + "\n")
            
        logger.info(f"Telemetry logged for agent: {result.agent_name}")
    except Exception as e:
        logger.error(f"Failed to log telemetry: {e}")
