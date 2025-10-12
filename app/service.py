from datetime import datetime, timedelta, timezone
from pprint import pprint

from worlds_api_client import WorldsAPIClient
from db.crud import store_tags_series, store_top_tracks, store_zones, save_devices

def aggregate_tracks(client: WorldsAPIClient, data_source_id: str, minutes: int = 60, max_tracks: int = 5):
    """
    Aggregate track data from Worlds API for a given device/data_source.
    Returns structured payloads for tags, top tracks, and zones.
    """
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

    # --- Aggregation containers ---
    tag_counts = {}
    track_details = {}
    all_zones = set()

    after_cursor = None
    seen_cursors = set()

    while True:
        if after_cursor:
            variables["after"] = after_cursor

        page = client.execute_query("tracks", variables)
        nodes = client.extract_nodes(page)

        for node in nodes:
            tag = node.get("tag", "unknown")
            track_id = node.get("id")
            start = node.get("startTime")
            end = node.get("endTime")
            detections = node.get("detections", [])
            video = node.get("video", {})
            thumbnail = video.get("thumbnailUrl")

            # --- Track length ---
            try:
                start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                length_sec = (end_dt - start_dt).total_seconds()
            except Exception:
                length_sec = 0.0

            # --- Average confidence ---
            conf_vals = [
                d.get("metadata", {}).get("track_confidence")
                for d in detections
                if d.get("metadata", {}).get("track_confidence") is not None
            ]
            avg_conf = sum(conf_vals) / len(conf_vals) if conf_vals else None

            # --- Zones ---
            zones = {z["name"] for d in detections for z in d.get("zones", []) if z.get("name")}
            all_zones.update(zones)

            # --- Tag counts ---
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # --- Track details ---
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

        # --- Pagination check ---
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

    # --- Prepare final outputs ---
    # Tags
    tags_output = {
        **base_record,
        "tags": [{"tag": t, "count": c} for t, c in sorted(tag_counts.items(), key=lambda kv: kv[1], reverse=True)]
    }

    # Top tracks: keep top N longest
    sorted_tracks = sorted(track_details.values(), key=lambda x: x["length"], reverse=True)[:max_tracks]

    # Zones
    zones_output = {
        **base_record,
        "zones": sorted(list(all_zones))
    }

    # --- Persist to DB ---
    store_tags_series(tags_output)
    store_top_tracks(data_source_id, sorted_tracks)
    store_zones(data_source_id, zones_output["zones"], zones_output["timestamp"])

    return {
        "tags": tags_output,
        "top_tracks": sorted_tracks,
        "zones": zones_output
    }

def get_devices_list(client):
    flattened_list = []
    variables = client.get_default_variables()
    variables['filter'] = {
        "address": {"like": "earthcam"},
    }

    devices = client.execute_query("devices", variables)
    for item in client.extract_nodes(devices):
        ds = item.pop('dataSource')
        flattened_list.append({**item, **ds})

    return flattened_list

def main() :
    client = WorldsAPIClient()
    data_source_id = "4ae953d5-d3a6-4f70-8b5a-0873a40f518b"

    devices = get_devices_list(client)
    pprint(devices)
    save_devices(devices)
    result = aggregate_tracks(client, data_source_id, minutes=60, max_tracks=5)
    pprint(result)

    #tracks = get_top_tracks(data_source_id)
    #pprint(tracks)

main()
