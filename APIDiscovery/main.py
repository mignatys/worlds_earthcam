from discovery import WorldsAPIDiscovery
import os
from dotenv import load_dotenv

# initialize helper
load_dotenv()
api_url = os.getenv("WORLDS_API_URL")
token_id = os.getenv("WORLDS_TOKEN_ID")
token_value = os.getenv("WORLDS_TOKEN_VALUE")

helper = WorldsAPIDiscovery(api_url, token_id, token_value)

# Variables example for a 24h time window

variables = {
    "filter": "FilterDataSourceInput!",
    "first": "Int!"
}
query = helper.build_query_all_fields("detections", "DetectionEdge", variables)
print("Generated Query:")
print(query)

# Execute query with actual variable values
vars_values = {
    "filter": {
        "time": {
            "between": ["2025-10-06T00:00:00.000+00", "2025-10-06T23:59:59.000+00"]
        }
    },
    "first": 5
}
#response = helper.execute_query(query, vars_values)
#print("Response:")
#print(response)