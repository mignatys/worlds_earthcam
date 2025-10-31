# Take home Interview assignment from Worlds.io
Worlds API consumes a video stream and provides analytics on objects and scense observed in the video<br>
The project below demonstrates:
- integration with WORLDS GraphQL endpoint to consume fata
- subscription to a stream
- producing alerts for yellow vests
- generation of mutations to provide feedback to the API
- data agregation of consumed data
- generation and storage of timeseries in DB
- Docker containeresation
- Displaying data in human readable format in Graphana

# worlds_earthcam
worlds.io earthcam object tracking and stats

1) To run the project you need to supply token id and value in ./app/.env file

WORLDS_TOKEN_ID=<token_id>
WORLDS_TOKEN_VALUE=<toke_value>

2) docker-compose up -build

# Project description

Dashboard(Demo):
https://worlds.miglabs.org/d/ad2pz54/worlds-io?orgId=1&from=now-3h&to=now&timezone=browser

System components:

- app/subscription_service
- app/dahsboard_service
- postgres database
- graphana dahsbard

Subscription service

- subscribes to detections and populates detection_events table (db keeps 24 hours of data only)
- commits batches of 300 detections to db
- aggregates the number of times the tags were seen in the batch, then commits to preserve space
- monitors for yellow_vest and creates an entry in the events table for each observation
- This was the place where I originally produced Event mutations, but there were too many.
- commented out that section and only insert in the db now to not pollute worlds.io db.
- produced mutations have metadata : {name: "Michael Ignatysh"} and a custom producer
- custom producer: 1514aad2-bd89-42ab-8831-3ec75866a929
- populates the Detections time series and yellow vest detection count widgets in grafana dashboard

Dashboard service

- Runs once an hour against Tracks for a sourceId, pulls 1 hour of data, while consuming all api pages.
- Populates zones table with a list of zones seen over the last hour (replaced every hour)
- populates top_tracks table with top 5 longest tracks based on track duration (replaced every hour)
- populates tags_series table. Each entry shows the count of tags over the last hour (accumulates series)
- populates total tags, total tags time series, top5 tracks, and observed zones widgets in grafana

grafana

- See statistic for Burbon Street Camera (The only Earthcam with data stream)
