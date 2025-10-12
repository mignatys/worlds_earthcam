from sqlalchemy.orm import Session
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from .model import TagsSeries, TopTracks, Zones, Alerts, Devices
from .db import SessionLocal


def get_devices(device_id: str = None):
    """Fetch a single device by id or all devices."""
    with SessionLocal() as db:
        query = db.query(Devices)
        if device_id:
            return query.filter(Devices.device_id == device_id).first()
        return query.all()

def save_devices(devices: list):
    if not devices:
        return

    with SessionLocal() as db:
        ids = [d['id'] for d in devices]
        if ids:
            db.query(Devices).filter(Devices.id.in_(ids)).delete(synchronize_session=False)
        db.bulk_insert_mappings(Devices, devices)
        db.commit()


def store_tags_series(data: dict):
    with SessionLocal() as db:
        entry = TagsSeries(**data)
        db.add(entry)
        db.commit()

def store_top_tracks(device_id: str, tracks: list):
    """
    Delete old tracks for device_id and insert new top tracks.
    Each track in `tracks` is a dict with keys matching TopTracks fields.
    """
    with SessionLocal() as db:
        # delete old tracks
        db.execute(delete(TopTracks).where(TopTracks.device_id == device_id))
        # insert new tracks
        for track in tracks:
            db.add(TopTracks(**track))
        db.commit()

def get_top_tracks(device_id: str):
    with SessionLocal() as db:
        tracks = (
            db.query(TopTracks)
            .filter(TopTracks.device_id == device_id)
            .all()
        )
        return tracks


def store_zones(device_id: str, zones: list, timestamp=None):
    timestamp = timestamp or datetime.utcnow()
    with SessionLocal() as db:
        db.merge(Zones(device_id=device_id, zones=zones, timestamp=timestamp))
        db.commit()

def store_alert(data: dict):
    with SessionLocal() as db:
        entry = Alerts(**data)
        db.add(entry)
        db.commit()
