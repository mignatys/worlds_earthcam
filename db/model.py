from sqlalchemy import Column, String, Integer, JSON, TIMESTAMP, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class TagsSeries(Base):
    __tablename__ = "tags_series"
    id = Column(Integer, primary_key=True)
    device_id = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True))
    tags = Column(JSON)

class TopTracks(Base):
    __tablename__ = "top_tracks"
    id = Column(String, primary_key=True)
    device_id = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True))
    length = Column(Float)
    detections = Column(Integer)
    tag = Column(String)
    thumbnail_url = Column(String)
    track_confidence_average = Column(Float)
    zones = Column(JSON)

class Zones(Base):
    __tablename__ = "zones"
    device_id = Column(String, primary_key=True)
    timestamp = Column(DateTime(timezone=True))
    zones = Column(JSON)

class Alerts(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    device_id = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True))
    tag = Column(String)
    detection = Column(JSON)

class Devices(Base):
    __tablename__ = "devices"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String)

class DetectionActivity(Base):
    __tablename__ = 'detection_events'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True))
    source_id = Column(String, nullable=False)
    source_name = Column(String, nullable=False)
    tag = Column(String)
    event_count = Column(Integer, default=1)

class Events(Base):
    __tablename__ = "events"
    id = Column(String, primary_key=True) # Changed from Integer to String
    event_producer_id = Column(String, nullable=False)
    type = Column(String, nullable=False)
    sub_type = Column(String, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    draft = Column(Boolean, nullable=False)
    priority = Column(String, nullable=False)
    metadata_ = Column("metadata", JSON, key="metadata_")
