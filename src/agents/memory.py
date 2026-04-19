import sqlite3
import json
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from src.agents.protocols import Signal, AgentOpinion
from src.utils.cache import CacheConfig

logger = logging.getLogger(__name__)

class AgentMemory:
    """
    Handles storing and retrieving analysis history to provide context and calibrate confidence.
    Uses SQLite for persistence.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or CacheConfig.DB_PATH
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the analysis_history table if it doesn't exist."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    signal TEXT NOT NULL,
                    price REAL,
                    opinion TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_symbol ON analysis_history(symbol)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON analysis_history(timestamp)')

    def save_analysis(self, symbol: str, signal: Signal, price: float, opinion: AgentOpinion):
        """Save a new analysis result to history."""
        try:
            opinion_json = opinion.model_dump_json() if hasattr(opinion, 'model_dump_json') else json.dumps(opinion)
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''
                    INSERT INTO analysis_history (symbol, signal, price, opinion)
                    VALUES (?, ?, ?, ?)
                ''', (symbol, signal.value, price, opinion_json))
            logger.info(f"Saved analysis history for {symbol}")
        except Exception as e:
            logger.error(f"Failed to save analysis for {symbol}: {e}")

    def get_recent_history(self, symbol: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Retrieve recent analysis history for a given symbol."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT signal, price, opinion, timestamp
                    FROM analysis_history
                    WHERE symbol = ?
                    ORDER BY timestamp DESC, id DESC
                    LIMIT ?
                ''', (symbol, limit))
                rows = cursor.fetchall()
                
                history = []
                for row in rows:
                    item = dict(row)
                    try:
                        item['opinion'] = json.loads(item['opinion'])
                    except:
                        pass
                    history.append(item)
                return history
        except Exception as e:
            logger.error(f"Failed to fetch history for {symbol}: {e}")
            return []

    def calculate_accuracy(self, symbol: str) -> Dict[str, float]:
        """
        Placeholder logic for calculating agent accuracy.
        In the future, this will compare historical signals with subsequent price action.
        """
        # For now, return a default calibration
        return {
            "historical_accuracy": 0.75,
            "sample_size": 0
        }
