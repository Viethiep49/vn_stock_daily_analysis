import pytest
import os
from pathlib import Path
from src.agents.memory import AgentMemory
from src.agents.protocols import Signal, AgentOpinion

def test_agent_memory_flow():
    # Use a temporary database for testing
    test_db = Path(".cache/test_memory.db")
    if test_db.exists():
        test_db.unlink()
    
    memory = AgentMemory(db_path=test_db)
    
    symbol = "VNM"
    signal = Signal.BUY
    price = 75000.0
    opinion = AgentOpinion(
        signal=signal,
        confidence=0.8,
        reasoning="Testing memory"
    )
    
    # 1. Save analysis
    memory.save_analysis(symbol, signal, price, opinion)
    
    # 2. Retrieve history
    history = memory.get_recent_history(symbol)
    assert len(history) == 1
    assert history[0]['signal'] == "BUY"
    assert history[0]['price'] == 75000.0
    assert history[0]['opinion']['confidence'] == 0.8
    
    # 3. Multiple entries
    memory.save_analysis(symbol, Signal.HOLD, 76000.0, opinion)
    history = memory.get_recent_history(symbol, limit=5)
    assert len(history) == 2
    assert history[0]['signal'] == "HOLD" # Most recent first
    
    # Cleanup
    if test_db.exists():
        test_db.unlink()

if __name__ == "__main__":
    test_agent_memory_flow()
    print("AgentMemory test passed!")
