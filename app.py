from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # ADD THIS
import httpx
from datetime import datetime
import asyncio

app = FastAPI()

# ADD THIS CORS MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

START_DATE = datetime(2026, 5, 10)
INITIAL_DAYS = 1000

def get_remaining_days():
    days_passed = (datetime.now().date() - START_DATE.date()).days
    return max(0, INITIAL_DAYS - days_passed)

async def keep_alive():
    while True:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(
                    "https://aadharfam.onrender.com/full-search?aadhaar=402176230714"
                )
                print(f"[PING] Status: {r.status_code}")
        except Exception as e:
            print(f"[PING ERROR] {e}")

        await asyncio.sleep(160)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(keep_alive())

@app.get("/full-search")
async def full_search(aadhaar: str = Query(...)):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            original_response = await client.get(
                "https://atof.onrender.com/full-search",
                params={"aadhaar": aadhaar}
            )
            original_response.raise_for_status()
        except httpx.TimeoutException:
            return JSONResponse({"error": "Upstream API timed out"}, status_code=504)
        except httpx.HTTPStatusError as e:
            return JSONResponse(
                {"error": f"Upstream returned {e.response.status_code}", "detail": e.response.text[:300]},
                status_code=502
            )
        except httpx.RequestError as e:
            return JSONResponse({"error": f"Connection failed: {str(e)}"}, status_code=502)

        try:
            original_data = original_response.json()
        except Exception:
            return JSONResponse(
                {"error": "Upstream returned non-JSON", "body": original_response.text[:300]},
                status_code=502
            )

    original_data["remaining_days"] = get_remaining_days()
    
    # Add CORS headers manually (backup)
    return JSONResponse(
        content=original_data,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Add OPTIONS handler for preflight requests
@app.options("/full-search")
async def options_full_search():
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400",
        }
    )

@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                "https://atof.onrender.com/full-search",
                params={"aadhaar": "test"}
            )
            return {
                "upstream_status": r.status_code,
                "remaining_days": get_remaining_days()
            }
    except Exception as e:
        return {"error": str(e)}
