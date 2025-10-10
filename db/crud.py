from sqlalchemy.orm import Session
from sqlalchemy import delete
from .model import TagsSeries, TopTracks, Zones, Alerts
from .db import SessionLocal

def store_tags_series(data: dict):
    with SessionLocal() as db:
        entry = TagsSeries(**data)
        db.add(entry)
        db.commit()

def store_top_tracks(deviceId: str, tracks: list):
    """
    Delete old tracks for deviceId and insert new top tracks.
    Each track in `tracks` is a dict with keys matching TopTracks fields.
    """
    with SessionLocal() as db:
        # delete old tracks
        db.execute(delete(TopTracks).where(TopTracks.deviceId == deviceId))
        # insert new tracks
        for track in tracks:
            db.add(TopTracks(**track))
        db.commit()

def store_zones(deviceId: str, zones: list, timestamp=None):
    """
    Upsert zones for deviceId
    """
    with SessionLocal() as db:
        existing = db.get(Zones, deviceId)
        if existing:
            existing.zones = zones
            if timestamp:
                existing.timestamp = timestamp
        else:
            db.add(Zones(deviceId=deviceId, zones=zones, timestamp=timestamp))
        db.commit()

def store_alert(data: dict):
    with SessionLocal() as db:
        entry = Alerts(**data)
        db.add(entry)
        db.commit()
