from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import asyncio

app = FastAPI(title="Aadhaar Proxy API with Remaining Days")

# Target API endpoint
TARGET_API = "https://atof.onrender.com/full-search"

# Setting initial days to 30 (can be adjusted)
INITIAL_DAYS = 30
START_DATE = datetime.now().date()  # API starts from today

def calculate_remaining_days() -> int:
    """Calculate remaining days based on start date"""
    today = datetime.now().date()
    days_passed = (today - START_DATE).days
    remaining = max(0, INITIAL_DAYS - days_passed)
    return remaining

async def fetch_original_data(aadhaar: str) -> Dict[str, Any]:
    """Fetch data from the original API"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(TARGET_API, params={"aadhaar": aadhaar})
        response.raise_for_status()
        return response.json()

def add_remaining_days_to_response(original_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add remaining days field to the original response"""
    remaining_days = calculate_remaining_days()
    
    # Create a new response with remaining days added
    enhanced_response = {
        "remaining_days": remaining_days,
        **original_data  # Spread original data
    }
    return enhanced_response

@app.get("/full-search")
async def proxy_full_search(aadhaar: str = Query(..., description="Aadhaar number")):
    """
    Proxy endpoint that fetches data from original API and adds remaining days
    """
    try:
        # Fetch original data
        original_data = await fetch_original_data(aadhaar)
        
        # Add remaining days and return
        enhanced_data = add_remaining_days_to_response(original_data)
        
        return JSONResponse(content=enhanced_data)
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Upstream API error: {e.response.text}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Failed to reach upstream API: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/remaining-days")
async def get_remaining_days():
    """Endpoint to check only remaining days"""
    return {"remaining_days": calculate_remaining_days()}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "remaining_days": calculate_remaining_days(),
        "start_date": START_DATE.isoformat(),
        "initial_days": INITIAL_DAYS
    }

# Optional: Root endpoint with API info
@app.get("/")
async def root():
    return {
        "message": "Aadhaar Proxy API with Remaining Days",
        "endpoints": {
            "/full-search": "GET - Pass aadhaar parameter",
            "/remaining-days": "GET - Check remaining days only",
            "/health": "GET - Health check"
        },
        "example": "/full-search?aadhaar=202372727238",
        "remaining_days_initial": INITIAL_DAYS,
        "remaining_days_current": calculate_remaining_days()
    }

# To run: uvicorn main:app --reload --port 8000
