import os
import asyncio
import requests
from dotenv import load_dotenv

from gql import Client, gql
from gql.transport.websockets import WebsocketsTransport

from typing import Callable, Optional

load_dotenv()

class WorldsAPIClient:
    def __init__(self):
        self.api_url = os.getenv("WORLDS_API_URL")
        self.ws_url = os.getenv("WORLDS_WS_URL")
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

    def execute_mutation(self, mutation_name: str, variables: dict = None) -> dict:
        """
        Executes a GraphQL mutation and returns the result.
        """
        mutation_str = self.load_query(mutation_name)
        payload = {"query": mutation_str}
        if variables:
            payload["variables"] = variables

        response = requests.post(self.api_url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

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

    async def subscribe(self, query_name: str, variables: dict = None, callback: Optional[Callable] = None):
        transport = WebsocketsTransport(
            url=self.ws_url,
            subprotocols=[WebsocketsTransport.GRAPHQLWS_SUBPROTOCOL],
            init_payload={
                "x-token-id": self.token_id,
                "x-token-value": self.token_value
            }
        )

        async with Client(transport=transport, fetch_schema_from_transport=False) as session:
            query_str = self.load_query(query_name)
            subscription = gql(query_str)

            async for result in session.subscribe(subscription, variable_values=variables or {}):
                if callback:
                    callback(result)
                else:
                    print("New subscription event:", result)