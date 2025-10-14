from sqlalchemy.orm import Session
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from .model import TagsSeries, TopTracks, Zones, Alerts, Devices, DetectionActivity, Events
from .db import SessionLocal
from datetime import datetime


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


def store_event(event_data: dict):
    """
    Transforms and upserts an event into the database by modifying the dict in-place.
    Assumes 'event_producer_id' is already present in the dictionary.
    """
    if 'id' not in event_data:
        raise ValueError("Event data must include an 'id'")

    if 'metadata' in event_data:
        event_data['metadata_'] = event_data.pop('metadata')
    if 'subType' in event_data:
        event_data['sub_type'] = event_data.pop('subType')
    if 'startTime' in event_data:
        event_data['start_time'] = datetime.fromisoformat(event_data.pop('startTime').replace("Z", "+00:00"))
    if 'endTime' in event_data:
        event_data['end_time'] = datetime.fromisoformat(event_data.pop('endTime').replace("Z", "+00:00"))

    with SessionLocal() as db:
        event_to_save = Events(**event_data)
        db.merge(event_to_save)
        db.commit()
        print(f"Successfully saved event {event_data.get('id')}")


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

def store_detection_activity_bulk(data_list: list):
    if not data_list:
        return

    for data in data_list:
        if 'event_count' not in data:
            data['event_count'] = 1

    with SessionLocal() as db:
        db.bulk_insert_mappings(DetectionActivity, data_list)
        db.commit()
