import os
import requests
from dotenv import load_dotenv

load_dotenv()

class WorldsAPIClient:
    def __init__(self):
        self.api_url = os.getenv("WORLDS_API_URL")
        self.token_id = os.getenv("WORLDS_TOKEN_ID")
        self.token_value = os.getenv("WORLDS_TOKEN_VALUE")
        self.headers = {
            "x-token-id": self.token_id,
            "x-token-value": self.token_value,
            "Content-Type": "application/json"
        }

    """
    Load a GraphQL query from ./queries/<name>.graphql
    """
    def load_query(self, name: str) -> str:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "queries", f"{name}.graphql")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Query file not found: {path}")
        with open(path, "r") as f:
            return f.read()

    def execute_query(self, query_name: str, variables: dict = None) -> list[dict]:
        query_str = self.load_query(query_name)
        payload = {"query": query_str}
        if variables:
            payload["variables"] = variables
        response = requests.post(self.api_url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def get_default_variables(self):
        return {
            "filter": {},
            "first": 50,
            "after": None,
            "sort": []
        }

    @staticmethod
    def extract_nodes(api_response: dict) -> list[dict]:
        result = []
        data = api_response.get("data", {})

        for key, value in data.items():
            edges = value.get("edges", [])
            for edge in edges:
                node = edge.get("node")
                if node:
                    result.append(node)
        return result
