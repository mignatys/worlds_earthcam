import time
import logging
from datetime import datetime, timedelta, timezone
from worlds_api_client import WorldsAPIClient
from db.crud import store_tags_series, store_top_tracks, store_zones, save_devices

logger = logging.getLogger(__name__)

# Configure logging for the daemon
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Main aggregation function for backend.
# Consumes tracks over the last hour, loops through paginated response.
# Aggregates the data to compute:
# 1) top 5 longest tracks by time
# 2) tag -> count over the last hour
# 3) zones over the last hour
#
# #2 (tags) are accumulated over time
# #1 and #3 replaced for each time window
def aggregate_tracks(client: WorldsAPIClient, data_source_id: str, minutes: int = 60, max_tracks: int = 5):
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=minutes)

    variables = client.get_default_variables()
    variables["filter"] = {
        "dataSourceId": {"eq": data_source_id},
        "time": {
            "between": [
                start_time.isoformat(timespec="milliseconds"),
                end_time.isoformat(timespec="milliseconds"),
            ]
        },
    }

    base_record = {
        "device_id": data_source_id,
        "timestamp": end_time.isoformat(timespec="seconds")
    }

    # Aggregated return data placeholders
    tag_counts = {}
    track_details = {}
    all_zones = set()

    after_cursor = None
    seen_cursors = set()

    while True:
        if after_cursor:
            variables["after"] = after_cursor

        try:
            page = client.execute_query("tracks", variables)
            nodes = client.extract_nodes(page)
        except Exception as e:
            logger.error(f"Failed to fetch tracks for {data_source_id}: {e}", exc_info=True)
            break

        for node in nodes:
            tag = node.get("tag", "unknown")
            track_id = node.get("id")
            start = node.get("startTime")
            end = node.get("endTime")
            detections = node.get("detections", [])
            video = node.get("video", {})
            thumbnail = video.get("thumbnailUrl")

            # Calculate track length
            try:
                start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                length_sec = (end_dt - start_dt).total_seconds()
            except Exception:
                length_sec = 0.0

            # Get average confidence for the track
            conf_vals = [
                d.get("metadata", {}).get("track_confidence")
                for d in detections
                if d.get("metadata", {}).get("track_confidence") is not None
            ]
            avg_conf = sum(conf_vals) / len(conf_vals) if conf_vals else None

            # Extract zones from detections
            zones = {z["name"] for d in detections for z in d.get("zones", []) if z.get("name")}
            all_zones.update(zones)

            tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # Build Top Tracks record
            track_details[track_id] = {
                "id": track_id,
                "device_id": data_source_id,
                "timestamp": base_record["timestamp"],
                "length": length_sec,
                "detections": len(detections),
                "tag": tag,
                "thumbnail_url": thumbnail,
                "track_confidence_average": avg_conf,
                "zones": list(zones),
            }

        # Pagination Voodoo
        page_info = None
        for v in page.get("data", {}).values():
            page_info = v.get("pageInfo")
            break

        if not page_info or not page_info.get("hasNextPage"):
            break

        end_cursor = page_info.get("endCursor")
        if not end_cursor or end_cursor in seen_cursors:
            break

        seen_cursors.add(end_cursor)
        after_cursor = end_cursor

    # Prepare records to store into DB
    tags_output = {**base_record, "tags": [{"tag": t, "count": c} for t, c in tag_counts.items()]}
    sorted_tracks = sorted(track_details.values(), key=lambda x: x["length"], reverse=True)[:max_tracks]
    zones_output = {**base_record, "zones": list(all_zones)}

    # Persist to DB
    try:
        store_tags_series(tags_output)
        store_top_tracks(data_source_id, sorted_tracks)
        store_zones(data_source_id, zones_output["zones"], zones_output["timestamp"])
    except Exception as e:
        logger.error(f"Failed to store aggregated data for {data_source_id}: {e}", exc_info=True)

    return {"tags": tags_output, "top_tracks": sorted_tracks, "zones": zones_output}


def get_devices_list(client):
    flattened_list = []
    variables = client.get_default_variables()
    variables['filter'] = {"address": {"like": "earthcam"}}
    try:
        devices = client.execute_query("devices", variables)
        for item in client.extract_nodes(devices):
            ds = item.pop('dataSource')
            flattened_list.append({**item, **ds})
    except Exception as e:
        logger.error(f"Failed to fetch devices: {e}", exc_info=True)
    return flattened_list


# Main daemon loop that runs the sync every hour.
def main():
    client = WorldsAPIClient()
    logger.info("Dashboard service started.")

    # Had this to display device dropdown in grafana and select dashboard per device
    # But since other sources produce no data this is pretty much useless
    # Keeping it here since the work has already been done
    try:
        logger.info("Fetching and saving device list...")
        devices = get_devices_list(client)
        if not devices:
            logger.warning("No devices returned from API. Skipping track aggregation for this cycle.")
            return

        save_devices(devices)
        logger.info(f"Successfully saved {len(devices)} devices.")
    except Exception as e:
        logger.error(f"A failure occurred while fetching devices: {e}", exc_info=True)

    # We will do this for Burbon Street only since other sources have no data
    device_id = "4ae953d5-d3a6-4f70-8b5a-0873a40f518b"
    while True:
        try:
            logger.info(f"Aggregating tracks for device_id: {device_id}")
            aggregate_tracks(client, device_id, minutes=60, max_tracks=5)
        except Exception as e:
            logger.critical(f"An unexpected critical error occurred in the main loop: {e}", exc_info=True)

        logger.info("Cycle finished. Sleeping for 1 hour.")
        time.sleep(3600)  # Sleep for 3600 seconds


if __name__ == "__main__":
    main()
