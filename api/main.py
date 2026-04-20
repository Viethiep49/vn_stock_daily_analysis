from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
import os
import sys

# Ensure src is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.factory import AnalyzerFactory
from src.data_provider.vnstock_provider import VNStockProvider
from datetime import datetime, timedelta

app = FastAPI(title="VN Stock Daily Analysis API")

# Initialize data provider
data_provider = VNStockProvider()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for streaming content
analysis_stream_cache = {}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/history")
async def get_history(symbol: str, days: int = 100):
    try:
        end_date = datetime.today().strftime('%Y-%m-%d')
        start_date = (datetime.today() - timedelta(days=days)).strftime('%Y-%m-%d')
        df = data_provider.get_historical_data(symbol, start=start_date, end=end_date)
        
        if df.empty:
            return []
            
        # Convert df to list of dicts for FE (O, H, L, C, V, Date)
        history = []
        for _, row in df.iterrows():
            history.append({
                "date": str(row['date']),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": int(row['volume'])
            })
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze(request: Request):
    try:
        data = await request.json()
        symbol = data.get("symbol", "").upper()
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
        
        use_agents = data.get("use_agents", True)
        skill = data.get("skill")
        
        analyzer = AnalyzerFactory.create(use_agents=use_agents, skill=skill)
        result = analyzer.analyze(symbol)
        
        if result.get("status") == "success":
            quote = result.get("quote", {})
            # Rename quote keys for frontend
            if "change_pct" in quote:
                quote["percent_change"] = quote.pop("change_pct")
            if "price" in quote:
                quote["last_price"] = quote.pop("price")

            report = result.get("report", {})
            indicators = result.get("indicators", {})

            # Build opinion object from report + indicators
            cards = report.get("cards", []) if isinstance(report, dict) else []
            ind = indicators if isinstance(indicators, dict) else {}
            r1 = ind.get("resistance_20", 0)
            s1 = ind.get("support_20", 0)

            opinion = {
                "signal": report.get("final_signal", "HOLD") if isinstance(report, dict) else "HOLD",
                "confidence": (report.get("composite", 50) / 100) if isinstance(report, dict) else 0.5,
                "sentiment_score": (report.get("composite", 50) / 100) if isinstance(report, dict) else 0.5,
                "reasoning": result.get("llm_analysis", ""),
                "key_points": [c.get("reason", "") for c in cards if c.get("reason")][:5],
                "key_levels": {
                    "resistance_1": round(r1, 2),
                    "resistance_2": round(r1 * 1.03, 2) if r1 else 0,
                    "support_1": round(s1, 2),
                    "support_2": round(s1 * 0.97, 2) if s1 else 0,
                },
            }

            analysis_stream_cache[symbol] = result.get("llm_analysis", "")

            return {
                "symbol": result["symbol"],
                "status": "success",
                "info": result.get("info", {}),
                "quote": quote,
                "llm_analysis": result.get("llm_analysis", ""),
                "tech_summary": result.get("tech_summary", ""),
                "opinion": opinion,
                "is_multi_agent": use_agents,
            }

        return result
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyze/stream")
async def analyze_stream(symbol: str):
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol is required")
        
    async def event_generator():
        content = analysis_stream_cache.get(symbol)
        
        # If content isn't ready, wait a bit (basic polling simulation)
        retries = 0
        while not content and retries < 10:
            await asyncio.sleep(1)
            content = analysis_stream_cache.get(symbol)
            retries += 1
            
        if not content:
            yield {"data": "Phân tích đang được xử lý hoặc không tìm thấy..."}
            yield {"data": "[DONE]"}
            return

        # Simulate streaming by chunking words
        # This keeps src/ unchanged while providing the requested FE experience
        tokens = content.split(' ')
        for token in tokens:
            yield {"data": token + " "}
            await asyncio.sleep(0.02)  # Controlled speed for readability
            
        yield {"data": "[DONE]"}

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
