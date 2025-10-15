# worlds_earthcam
worlds.io earthcam object tracking and stats

1) To run the project you need to supply ./app/.env file in the project of the following content:

WORLDS_API_URL=https://graphql.microsoft.worlds.io/graphql
WORLDS_WS_URL=wss://graphql.microsoft.worlds.io/graphql
WORLDS_TOKEN_ID=<token_id>
WORLDS_TOKEN_VALUE=<toke_value>
DATABASE_URL=postgresql+asyncpg://worlds:worlds_pass@postgres:5432/worldsdb
SYNC_DATABASE_URL=postgresql://worlds:worlds_pass@postgres:5432/worldsdb  # for Streamlit (psycopg2)

POSTGRES_USER=grafana
POSTGRES_PASSWORD=grafana
POSTGRES_DB=worlds
POSTGRES_HOST=worlds_postgres

2) docker-compose up -build
