from itertools import count

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from dashboard_service import get_devices_list, aggregate_tracks
from worlds_api_client import WorldsAPIClient

app = FastAPI(title="Worlds AI API Demo")

@app.get("/devices")
def get_devices():
    client = WorldsAPIClient()
    devices = get_devices_list(client)
    return JSONResponse(content=devices)

@app.get("/track/{device_id}")
async def get_tracks(device_id: str, interval: int = Query(10)):
    client = WorldsAPIClient()
    data = aggregate_tracks(client, device_id, interval)
    tags = []
    for key, val in data['tags'].items():
        tags.append({
            "tag": key,
            "count" :val['count'],
            "longest_track": val['longest_track']
        })
    data['tags'] = tags
    return JSONResponse(content=data)
