from sqlalchemy import Column, String, Integer, JSON, TIMESTAMP, Float, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class TagsSeries(Base):
    __tablename__ = "tags_series"
    id = Column(Integer, primary_key=True)
    device_id = Column(String, index=True)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    tags = Column(JSON)

class TopTracks(Base):
    __tablename__ = "top_tracks"
    id = Column(String, primary_key=True)
    device_id = Column(String, index=True)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    length = Column(Float)
    detections = Column(Integer)
    tag = Column(String)
    thumbnail_url = Column(String)
    track_confidence_average = Column(Float)
    zones = Column(JSON)

class Zones(Base):
    __tablename__ = "zones"
    device_id = Column(String, primary_key=True)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    zones = Column(JSON)

class Alerts(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    device_id = Column(String, index=True)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    tag = Column(String)
    detection = Column(JSON)

class Devices(Base):
    __tablename__ = "devices"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String)
