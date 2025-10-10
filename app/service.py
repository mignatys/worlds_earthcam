from worlds_api_client import WorldsAPIClient
from datetime import datetime, timedelta, timezone
from pprint import pprint
from database import get_db

def aggregate_tracks(client, data_source_id: str, minutes: int = 60, max_tracks: int = 10):
    """
    Aggregate track data for a given data_source_id and time range (in minutes).
    Processes results page-by-page, keeping only top `max_tracks` longest tracks
    or one per tag if there are more than max_tracks tags.
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

    result = {
        "tags": {},
        "tracks": {},
        "dataSourceId": data_source_id,
        "time": end_time.timestamp()
    }

    after_cursor = None
    seen_cursors = set()

    def _process_page(nodes):
        for node in nodes:
            tag = node.get("tag", "unknown")
            track_id = node.get("id")
            start = node.get("startTime")
            end = node.get("endTime")
            detections = node.get("detections", [])
            video = node.get("video", {})
            thumbnail = video.get("thumbnailUrl")

            # --- track length ---
            try:
                start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                length_sec = (end_dt - start_dt).total_seconds()
            except Exception:
                length_sec = 0.0

            # --- average confidence ---
            confidence_values = [
                d.get("metadata", {}).get("track_confidence")
                for d in detections
                if d.get("metadata", {}).get("track_confidence") is not None
            ]
            avg_conf = sum(confidence_values) / len(confidence_values) if confidence_values else None

            # --- zones ---
            zones = {z["name"] for d in detections for z in d.get("zones", []) if z.get("name")}

            # --- update tags info ---
            if tag not in result["tags"]:
                result["tags"][tag] = {"count": 0, "longest_track": None, "longest_length": 0.0}
            result["tags"][tag]["count"] += 1
            if length_sec > result["tags"][tag]["longest_length"]:
                result["tags"][tag]["longest_length"] = length_sec
                result["tags"][tag]["longest_track"] = track_id

            # --- store track info ---
            result["tracks"][track_id] = {
                "thumbnailUrl": thumbnail,
                "length": length_sec,
                "detections": len(detections),
                "tag": tag,
                "track_confidence_average": avg_conf,
                "zones": list(zones),
            }

    # --- pagination loop ---
    while True:
        if after_cursor:
            variables["after"] = after_cursor
        page = client.execute_query("tracks", variables)
        nodes = client.extract_nodes(page)
        _process_page(nodes)

        # --- get pageInfo safely ---
        page_info = None
        data = page.get("data", {})
        for v in data.values():
            page_info = v.get("pageInfo")
            break

        print(f"Page fetched, nodes: {len(nodes)}, after_cursor: {after_cursor}")

        if not page_info or not page_info.get("hasNextPage"):
            break

        end_cursor = page_info.get("endCursor")
        if not end_cursor or end_cursor in seen_cursors:
            break
        seen_cursors.add(end_cursor)
        after_cursor = end_cursor

    # --- prune tracks to top N longest ---
    sorted_tracks = sorted(result["tracks"].items(), key=lambda kv: kv[1]["length"], reverse=True)
    keep_ids = set()
    # keep longest track per tag
    for tag, info in result["tags"].items():
        if info["longest_track"]:
            keep_ids.add(info["longest_track"])
    # keep top N overall
    keep_ids |= {tid for tid, _ in sorted_tracks[:max_tracks]}
    result["tracks"] = {tid: t for tid, t in result["tracks"].items() if tid in keep_ids}

    # --- remove helper longest_length from tags ---
    for tag in result["tags"]:
        result["tags"][tag].pop("longest_length", None)

    return result

def get_devices_list(client):
    variables = client.get_default_variables()
    variables['filter'] = {
        "address": {"like": "earthcam"},
    }
    devices = client.execute_query("devices", variables)
    return client.extract_nodes(devices)

def main() :
    '''
    client = WorldsAPIClient()
    db = get_db()

    pprint(get_device_list(client))


    data_source_id = "4ae953d5-d3a6-4f70-8b5a-0873a40f518b"
    res = aggregate_tracks(client, data_source_id, 60, 10)
    
    if res:
        tracks = db["tracks"]
        tracks.insert_one(res)
        print("Successfully inserted aggregated tracks into MongoDB.")

    pprint(res)





    tracks_var = client.get_default_variables()
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)
    variables['filter'] = {
            "dataSourceId": {"eq": data_source_id},
            "time": {
                "between": [
                    one_hour_ago.isoformat(timespec="milliseconds"),
                    now.isoformat(timespec="milliseconds")
                ]
            }
        }
    variables['first'] = 1
    tracks = client.execute_query("tracks", variables)
    print(devices)
    pprint(tracks)
    '''
main()
