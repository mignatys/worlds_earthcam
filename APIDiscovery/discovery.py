import requests
from graphql import get_introspection_query
from datetime import datetime, timedelta

class WorldsAPIDiscovery:
    def __init__(self, api_url, token_id, token_value):
        self.api_url = api_url
        self.headers = {
            "x-token-id": token_id,
            "x-token-value": token_value,
            "Content-Type": "application/json"
        }
        self.schema = self._fetch_schema()
        self.type_map = {t["name"]: t for t in self.schema["types"]}

    def _fetch_schema(self):
        query = {"query": get_introspection_query()}
        resp = requests.post(self.api_url, json=query, headers=self.headers)
        data = resp.json()
        if "data" not in data or "__schema" not in data["data"]:
            raise RuntimeError(f"Introspection failed, response: {data}")
        return data["data"]["__schema"]

    def get_type(self, type_name):
        return self.type_map.get(type_name)

    def list_fields_recursive(self, type_name, _visited=None, max_depth=5):
        """Return all fields recursively but safely."""
        if _visited is None:
            _visited = set()

        if type_name in _visited or max_depth <= 0:
            return {}

        type_obj = self.get_type(type_name)
        if not type_obj or "fields" not in type_obj:
            return {}

        _visited.add(type_name)
        fields = {}

        for f in type_obj["fields"]:
            f_type = f["type"]
            # Unwrap NonNull or List
            while f_type.get("ofType"):
                f_type = f_type["ofType"]

            nested_type = f_type.get("name")
            kind = f_type.get("kind")

            # Scalars and enums
            if kind in ["SCALAR", "ENUM"]:
                fields[f["name"]] = {}
            # Objects need subselection
            elif kind in ["OBJECT", "INTERFACE"] and self.get_type(nested_type):
                fields[f["name"]] = self.list_fields_recursive(
                    nested_type, _visited.copy(), max_depth - 1
                )
            # Lists of scalars? just include
            else:
                fields[f["name"]] = {}

        return fields

    def build_query_all_fields(self, query_name, type_name, variables=None):
        fields_dict = self.list_fields_recursive(type_name)
        field_str = self._build_field_string(fields_dict)
        var_def = self._build_variable_definitions(variables)
        var_use = self._build_variable_usage(variables)
        query = f"query {query_name}{var_def} {{\n  {query_name}({var_use}) {{\n{field_str}\n  }}\n}}"
        return query

    def _build_field_string(self, fields_dict, indent=4):
        lines = []
        for f, nested in fields_dict.items():
            if nested:
                nested_str = self._build_field_string(nested, indent + 2)
                lines.append(" " * indent + f + " {\n" + nested_str + "\n" + " " * indent + "}")
            else:
                lines.append(" " * indent + f)
        return "\n".join(lines)

    def _build_variable_definitions(self, variables):
        if not variables:
            return ""
        parts = [f"${name}: {v_type}" for name, v_type in variables.items()]
        return f"({', '.join(parts)})"

    def _build_variable_usage(self, variables):
        if not variables:
            return ""
        parts = [f"{name}: ${name}" for name in variables.keys()]
        return ", ".join(parts)

    def execute_query(self, query, variables=None):
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        resp = requests.post(self.api_url, headers=self.headers, json=payload)
        return resp.json()
