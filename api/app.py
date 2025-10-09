from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import random

app = FastAPI(title="Worlds AI API Demo")

# Simulated camera list
devices = [f"camera_{i}" for i in range(1, 11)]

@app.get("/devices")
async def get_devices():
    """Return list of camera devices."""
    return JSONResponse(content=devices)

@app.get("/track/{device_id}")
async def get_tracks(device_id: str, interval: int = Query(10)):
    """Return simulated track data for a camera."""
    data = {
        "device_id": device_id,
        "interval": interval,
        "tracks": [
            {
                "track_id": f"track_{i}",
                "label": random.choice(["car", "person", "dog", "truck"]),
                "detections": random.randint(10, 300),
                "image_url": f"https://picsum.photos/seed/{device_id}_{i}/120/80",
                "longest_track": round(random.uniform(5.0, 30.0), 2),
            }
            for i in range(10)
        ],
    }
    return JSONResponse(content=data)

