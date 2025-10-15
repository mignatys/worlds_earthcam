import asyncio
import logging
import uuid
from typing import List, Dict, Any
from datetime import datetime
from dateutil import parser

from worlds_api_client import WorldsAPIClient
from db.crud import store_detection_activity_bulk, store_event

logger = logging.getLogger(__name__)

AGGREGATE: Dict[str, Dict[str, Any]] = {}
BATCH_TIMEOUT = 30.0  # seconds

def prepare_detection_activity_for_db(event: Dict[str, Any]) -> Dict[str, Any]:
    #Transforms a raw detectionActivity event into a database-ready format.

    detection_activity = event.get("detectionActivity", {})
    track = detection_activity.get("track", {})
    data_source = track.get("dataSource", {})
    timestamp_str = detection_activity.get("timestamp")

    db_record = {
        "timestamp": parser.isoparse(timestamp_str) if timestamp_str else datetime.utcnow(),
        "source_id": data_source.get("id"),
        "source_name": data_source.get("name"),
        "tag": track.get("tag"),
        "event_count": 1,
    }

    if not db_record["source_id"] or not db_record["source_name"]:
        logger.error("Required fields 'source_id' or 'source_name' are missing. Skipping event.")
        return None

    return db_record

async def flush_aggregate():
    if not AGGREGATE:
        return

    batch = list(AGGREGATE.values())
    await asyncio.to_thread(store_detection_activity_bulk, batch)
    AGGREGATE.clear()

def alert_on_yellow_vest(detection: Dict[str, Any]):
    # If the event is for a 'yellow_vest', create and save a formal Event directly
    if detection["tag"] == "yellow_vest":
        try:
            #logger.error(f"MMM: {detection}")

            #start_time_iso = detection.get("timestamp")
            #start_time = datetime.fromisoformat(start_time_iso.replace("Z", "+00:00"))
            start_time = detection.get("timestamp")

            # DEPRECATED: Mutation block was removed to not pollute worlds.io DB
            # All alerts generated with producer_id below were auto inserted by
            # The mutation call below. This new producer was added using a mutation call

            # On yellow alert we create a mutation ot create an event
            # Then store the response of the mutation call with ID to the database for dashboard

            ########################################################################
            # result = client.execute_mutation("createEvent", variables=event_input)
            ########################################################################

            # Construct the event data dictionary for the database
            event_data = {
                "id": str(uuid.uuid4()),
                "event_producer_id": "1514aad2-bd89-42ab-8831-3ec75866a929",
                "type": "object-of-interest",
                "sub_type": "yellow_vest",
                "start_time": start_time,
                "end_time": start_time,
                "metadata_": {
                    "notes": "Detected person wearing yellow vest",
                    "name": "Michael Ignatysh"
                },
                "draft": False,
                "priority": "high"
            }

            # Save the event directly to the database
            store_event(event_data)
            logger.info(f"Created and saved event to DB: {event_data['id']}")
        except Exception as e:
            logger.error(f"Failed to create and save event: {e}", exc_info=True)

def handle_detection_activity(detection: Dict[str, Any]):
    try:
        db_record = prepare_detection_activity_for_db(detection)
        if not db_record:
            return

        # Aggregate detection activity in-memory. Count same tags into a single db entry for current bucket.
        tag = db_record["tag"]
        if tag not in AGGREGATE:
            AGGREGATE[tag] = db_record
        else:
            AGGREGATE[tag]["event_count"] += 1

        alert_on_yellow_vest(db_record)

    except Exception as e:
        logger.error(f"Error handling event: {e}", exc_info=True)

async def aggregate_flusher():
    #A background task that periodically flushes the aggregate buffer.
    while True:
        await asyncio.sleep(BATCH_TIMEOUT)
        await flush_aggregate()

async def main():
    logger.info("**Starting subscription service**")
    asyncio.create_task(aggregate_flusher())

    client = WorldsAPIClient()
    variables = {"filter": {}}

    while True:
        try:
            logger.info("Attempting to connect to event subscription...")
            await client.subscribe(
                "detectionActivity",
                variables=variables,
                callback=handle_detection_activity
            )
        except Exception as e:
            logger.error(f"Subscription connection lost: {e}. Reconnecting in 15 seconds...")
            await asyncio.sleep(15)
        else:
            logger.warning("Subscription ended gracefully. Reconnecting in 15 seconds...")
            await asyncio.sleep(15)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application shutting down.")
    except Exception as e:
        logger.critical(f"An unrecoverable error occurred: {e}", exc_info=True)
