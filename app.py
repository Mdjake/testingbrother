from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import httpx
from datetime import datetime

app = FastAPI()

# Fixed start date - days will count down from 30
START_DATE = datetime(2026, 5, 10)  # Today
INITIAL_DAYS = 30

def get_remaining_days():
    days_passed = (datetime.now().date() - START_DATE.date()).days
    return max(0, INITIAL_DAYS - days_passed)

@app.get("/full-search")
async def full_search(aadhaar: str = Query(...)):
    # 1. Fetch original API response (exact same)
    async with httpx.AsyncClient() as client:
        original_response = await client.get(
            "https://atof.onrender.com/full-search",
            params={"aadhaar": aadhaar}
        )
        original_data = original_response.json()
    
    # 2. Add remaining days field
    original_data["remaining_days"] = get_remaining_days()
    
    # 3. Return everything (original + new field at end)
    return JSONResponse(content=original_data)

# Run: uvicorn main:app --reload