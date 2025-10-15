import os
import asyncio
import requests
import logging
from dotenv import load_dotenv
from gql import Client, gql
from gql.transport.websockets import WebsocketsTransport
from typing import Callable, Optional

load_dotenv()
logger = logging.getLogger(__name__)

class WorldsAPIClient:
    def __init__(self):
        self.api_url = os.getenv("WORLDS_API_URL")
        self.ws_url = os.getenv("WORLDS_WS_URL")
        self.token_id = os.getenv("WORLDS_TOKEN_ID")
        self.token_value = os.getenv("WORLDS_TOKEN_VALUE")
        if not all([self.api_url, self.ws_url, self.token_id, self.token_value]):
            logger.warning("Some Worlds API environment variables are missing.")
        self.headers = {
            "x-token-id": self.token_id,
            "x-token-value": self.token_value,
            "Content-Type": "application/json"
        }

    def _load_query(self, name: str) -> str:
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "queries", f"{name}.graphql")
        if not os.path.exists(path):
            logger.error(f"Query file not found: {path}")
            raise FileNotFoundError(f"Query file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def _post(self, query_str: str, variables: Optional[dict] = None) -> dict:
        payload = {"query": query_str}
        if variables:
            payload["variables"] = variables
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            if "errors" in data:
                logger.warning(f"GraphQL returned errors: {data['errors']}")
            return data
        except requests.Timeout:
            logger.error("Request to Worlds API timed out.")
            raise
        except requests.RequestException as e:
            logger.error(f"HTTP request failed: {e}")
            raise

    def execute_query(self, query_name: str, variables: Optional[dict] = None) -> dict:
        query_str = self._load_query(query_name)
        return self._post(query_str, variables)

    def execute_mutation(self, mutation_name: str, variables: Optional[dict] = None) -> dict:
        mutation_str = self._load_query(mutation_name)
        return self._post(mutation_str, variables)

    @staticmethod
    def get_default_variables() -> dict:
        return {"filter": {}, "first": 50, "after": None, "sort": []}

    @staticmethod
    def extract_nodes(api_response: dict) -> list[dict]:
        result = []
        data = api_response.get("data", {})
        for value in data.values():
            edges = value.get("edges", [])
            for edge in edges:
                node = edge.get("node")
                if node:
                    result.append(node)
        return result

    async def subscribe(self, query_name: str, variables: Optional[dict] = None, callback: Optional[Callable] = None):
        transport = WebsocketsTransport(
            url=self.ws_url,
            subprotocols=[WebsocketsTransport.GRAPHQLWS_SUBPROTOCOL],
            init_payload={
                "x-token-id": self.token_id,
                "x-token-value": self.token_value,
            },
        )
        query_str = self._load_query(query_name)
        subscription = gql(query_str)
        try:
            async with Client(transport=transport, fetch_schema_from_transport=False) as session:
                async for result in session.subscribe(subscription, variable_values=variables or {}):
                    if callback:
                        try:
                            callback(result)
                        except Exception as cb_err:
                            logger.exception(f"Error in subscription callback: {cb_err}")
                    else:
                        logger.info(f"New subscription event: {result}")
        except asyncio.CancelledError:
            logger.info(f"Subscription cancelled for {query_name}")
        except Exception as e:
            logger.exception(f"Subscription error for {query_name}: {e}")
