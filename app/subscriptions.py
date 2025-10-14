import asyncio
import random

from worlds_api_client import WorldsAPIClient
import logging
from typing import List, Dict, Any
from datetime import datetime
from db.crud import store_detection_activity_bulk,  store_event
from dateutil import parser  # 💡 NEW: Used to parse the ISO 8601 timestamp string


client = WorldsAPIClient()

# -------------------------------------------------------------
# 🌟 Global Event Queue and Bulk Insert Configuration
# -------------------------------------------------------------

EVENT_QUEUE = asyncio.Queue()
BATCH_SIZE = 300
BATCH_TIMEOUT = 30.0

# -------------------------------------------------------------
# 🛠️ FIXED: Database Utility Functions
# -------------------------------------------------------------

def prepare_event_for_db(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms a raw event into a database-ready format by extracting nested fields.

    Sample Input Data Structure:
    {'detectionActivity': {'track': {'dataSource': {'id': '...', 'name': '...'}, 'tag': 'person'}, 'timestamp': '...Z'}}
    """

    # 🚨 FIX 1: Safely extract the nested detectionActivity block
    detection_activity = event.get("detectionActivity", {})
    track = detection_activity.get("track", {})
    data_source = track.get("dataSource", {})

    # 🚨 FIX 2: Create a dictionary that exactly matches the ORM model's fields
    # (except for 'id', which is auto-generated).

    # The 'timestamp' comes as an ISO string, so we must parse it to a datetime object.
    timestamp_str = detection_activity.get("timestamp")

    db_record = {
        # CRITICAL: The timestamp field must be present and a datetime object
        "timestamp": parser.isoparse(timestamp_str) if timestamp_str else datetime.utcnow(),

        # REQUIRED NOT NULL fields
        "source_id": data_source.get("id"),
        "source_name": data_source.get("name"),

        # OPTIONAL fields
        "tag": track.get("tag"),
        "event_count": 1,  # Defaulted as per your original logic

        # Use event_data_json if you still want the full raw event in the DB
        # This field isn't in your ORM model, but included for completeness if needed later
        # "event_data_json": json.dumps(event),
    }

    # IMPORTANT: The ORM will generate ID and the DB will reject if required fields are missing.
    # We must ensure source_id and source_name are not None before insertion.
    if not db_record["source_id"] or not db_record["source_name"]:
        logging.error("Required fields 'source_id' or 'source_name' are missing. Skipping event.")
        return None  # Skip this event if data is malformed

    return db_record


async def bulk_insert_events(events_list: List[Dict[str, Any]]):
    """
    Executes the synchronous bulk insert in a separate thread.
    """
    # Filter out any None records if prepare_event_for_db returned None
    clean_events_list = [e for e in events_list if e is not None]

    if not clean_events_list:
        return

    logging.info(f"💾 BULK INSERT: Submitting {len(clean_events_list)} events to a thread for DB write.")

    # Execute the synchronous DB function in a thread
    # This calls store_detection_activity_bulk(clean_events_list)
    await asyncio.to_thread(
        store_detection_activity_bulk,
        clean_events_list
    )

    # 🚨 FIX 3: Remove the simulated sleep/logging that was placed *after* # the real DB call, which was confusing the logs.
    logging.debug(f"✅ Bulk insert of {len(clean_events_list)} events committed via thread.")


# -------------------------------------------------------------
# 🚀 Background Worker Coroutine (The Consumer)
# -------------------------------------------------------------

async def event_db_worker():
    logging.info("⚙️ Database worker started.")
    current_batch = []

    while True:
        try:
            event = await asyncio.wait_for(
                EVENT_QUEUE.get(),
                timeout=BATCH_TIMEOUT
            )

            db_record = prepare_event_for_db(event)
            if db_record:  # Only append if preparation was successful
                current_batch.append(db_record)

            if len(current_batch) >= BATCH_SIZE:
                await bulk_insert_events(current_batch)
                current_batch = []

        except asyncio.TimeoutError:
            if current_batch:
                logging.debug(f"⏰ Timeout reached. Inserting partial batch of {len(current_batch)}.")
                await bulk_insert_events(current_batch)
                current_batch = []
            else:
                logging.debug("😴 Timeout reached. Queue is empty.")

        except Exception as e:
            logging.error(f"Worker failed to process batch: {e}", exc_info=True)
            current_batch = []


# -------------------------------------------------------------
# 📥 Event Handler (The Producer)
# -------------------------------------------------------------

def handle_event(event: Dict[str, Any]):
    try:
        EVENT_QUEUE.put_nowait(event)
        logging.debug(f"-> Event placed on queue. Queue size: {EVENT_QUEUE.qsize()}")

        detection_activity = event.get("detectionActivity", {})
        track = detection_activity.get("track", {})
        tag = track.get("tag")

        if tag == "yellow_vest":
            start_time = detection_activity.get("timestamp")
            event_input = {
                "event": {
                    "eventProducerId": "1514aad2-bd89-42ab-8831-3ec75866a929",
                    "type": "object-of-interest",
                    "subType": "yellow_vest",
                    "startTime": start_time,
                    "endTime": start_time,
                    "metadata": {
                        "notes": "Detected person wearing yellow vest",
                        "name": "Michael Ignatysh"
                    },
                    "draft": False,
                    "priority": "high"
                }
            }

            try:
                result = client.execute_mutation("createEvent", variables=event_input)
                event_data = result.get('data', {}).get('createEvent')
                if event_data:
                    event_data['event_producer_id'] = "1514aad2-bd89-42ab-8831-3ec75866a929"
                    store_event(event_data)
                    logging.info(f"Created Worlds Event: {result.get('data', {}).get('createEvent')}")
                else:
                    logging.error(f"Failed to create Worlds event: {result}")
                logging.info(f"Created Worlds Event: {result.get('data', {}).get('createEvent')}")

            except Exception as e:
                logging.error(f"Failed to create Worlds event: {e}", exc_info=True)

    except asyncio.QueueFull:
        logging.warning("[!] Queue is full! Dropping event to prevent memory overload.")


# -------------------------------------------------------------
# 🏁 Main Execution
# -------------------------------------------------------------

async def main():
    asyncio.create_task(event_db_worker())

    variables = {"filter": {}}
    logging.info("🌍 Starting event subscription...")
    await client.subscribe("detectionActivity", variables=variables, callback=handle_event)

    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    try:
        # 💡 NEW: Import required module for date parsing
        import dateutil.parser

        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Application shutting down.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)