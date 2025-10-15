import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict
from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from .model import TagsSeries, TopTracks, Zones, Devices, DetectionActivity, Events
from .db import SessionLocal


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def get_devices(device_id: Optional[str] = None) -> List[Devices]:
    with SessionLocal() as db:
        query = db.query(Devices)
        return query.filter(Devices.device_id == device_id).first() if device_id else query.all()


def save_devices(devices: List[Dict]):
    if not devices:
        logger.warning("save_devices called with empty device list.")
        return

    with SessionLocal() as db:
        try:
            ids = [d['id'] for d in devices if 'id' in d]
            if ids:
                db.query(Devices).filter(Devices.id.in_(ids)).delete(synchronize_session=False)
            db.bulk_insert_mappings(Devices, devices)
            db.commit()
            logger.info(f"Saved {len(devices)} devices.")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to save devices: {e}", exc_info=True)
            raise


def store_event(event_data: Dict):
    with SessionLocal() as db:
        try:
            db.merge(Events(**event_data))
            db.commit()
            logger.info(f"Event saved: {event_data.get('id')}")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error saving event {event_data.get('id')}: {e}", exc_info=True)
            raise


def store_tags_series(data: Dict):
    with SessionLocal() as db:
        try:
            db.add(TagsSeries(**data))
            db.commit()
            logger.info("Tag series entry stored.")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to store tags series: {e}", exc_info=True)
            raise


def store_top_tracks(device_id: str, tracks: List[Dict]):
    if not tracks:
        logger.warning(f"No tracks provided for device {device_id}")
        return

    with SessionLocal() as db:
        try:
            db.execute(delete(TopTracks).where(TopTracks.device_id == device_id))
            db.add_all([TopTracks(**track) for track in tracks])
            db.commit()
            logger.info(f"Stored {len(tracks)} top tracks for device {device_id}.")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to store top tracks for device {device_id}: {e}", exc_info=True)
            raise


def get_top_tracks(device_id: str) -> List[TopTracks]:
    with SessionLocal() as db:
        return db.query(TopTracks).filter(TopTracks.device_id == device_id).all()


def store_zones(device_id: str, zones: List[str], timestamp: Optional[datetime] = None):
    timestamp = timestamp or datetime.now(timezone.utc)
    with SessionLocal() as db:
        try:
            db.merge(Zones(device_id=device_id, zones=zones, timestamp=timestamp))
            db.commit()
            logger.info(f"Zones updated for device {device_id}.")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error storing zones for {device_id}: {e}", exc_info=True)
            raise


def store_detection_activity_bulk(data_list: List[Dict]):
    if not data_list:
        logger.warning("store_detection_activity_bulk called with empty data.")
        return

    with SessionLocal() as db:
        try:
            db.bulk_insert_mappings(DetectionActivity, data_list)
            db.commit()
            logger.info(f"Inserted {len(data_list)} detection activity entries.")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed bulk insert of detection activity: {e}", exc_info=True)
            raise
