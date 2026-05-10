from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
import httpx
from datetime import datetime
from datetime import timedelta

app = FastAPI()

# Fixed start date - days will count down from 30
START_DATE = datetime(2026, 5, 10)  # When API started
INITIAL_DAYS = 30

def get_remaining_days():
    """Calculate remaining days and raise exception if expired"""
    days_passed = (datetime.now().date() - START_DATE.date()).days
    remaining = INITIAL_DAYS - days_passed
    
    if remaining < 0:
        raise HTTPException(
            status_code=410, 
            detail="API Expired - 30 days period has ended"
        )
    return remaining

@app.get("/full-search")
async def full_search(aadhaar: str = Query(...)):
    # Check if API is expired first
    remaining_days = get_remaining_days()
    
    # Fetch original API response
    async with httpx.AsyncClient() as client:
        original_response = await client.get(
            "https://atof.onrender.com/full-search",
            params={"aadhaar": aadhaar}
        )
        original_data = original_response.json()
    
    # Add remaining days field
    original_data["remaining_days"] = remaining_days
    
    return JSONResponse(content=original_data)

@app.get("/remaining-days")
async def get_remaining_days_only():
    """Check remaining days only"""
    remaining_days = get_remaining_days()
    return {"remaining_days": remaining_days}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        remaining_days = get_remaining_days()
        return {
            "status": "healthy",
            "remaining_days": remaining_days,
            "start_date": START_DATE.isoformat(),
            "initial_days": INITIAL_DAYS,
            "expiry_date": (START_DATE + timedelta(days=INITIAL_DAYS)).isoformat()
        }
    except HTTPException as e:
        return {
            "status": "expired",
            "message": e.detail
        }

@app.get("/")
async def root():
    try:
        remaining_days = get_remaining_days()
        return {
            "message": "Aadhaar Proxy API with Remaining Days",
            "endpoints": {
                "/full-search": "GET - Pass aadhaar parameter",
                "/remaining-days": "GET - Check remaining days only",
                "/health": "GET - Health check"
            },
            "example": "/full-search?aadhaar=202372727238",
            "remaining_days_initial": INITIAL_DAYS,
            "remaining_days_current": remaining_days,
            "expiry_date": (START_DATE + timedelta(days=INITIAL_DAYS)).isoformat()
        }
    except HTTPException as e:
        return {
            "message": "API has expired",
            "detail": e.detail
        }

