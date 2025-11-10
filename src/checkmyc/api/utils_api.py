import os

from google.genai import types


class APIError(Exception):
    pass


class InvalidResponseError(APIError):
    pass


def check_api_key(env_var) -> str:
    key = os.getenv(env_var)
    if not key:
        raise OSError(f"Missing {env_var}")
    return key


def json_to_gemini_schema(node: dict) -> types.Schema:
    """Convert a JSON Schema Draft7-like dict to google.genai.types.Schema."""
    type_map = {
        "string": types.Type.STRING,
        "number": types.Type.NUMBER,
        "integer": types.Type.INTEGER,
        "boolean": types.Type.BOOLEAN,
        "array": types.Type.ARRAY,
        "object": types.Type.OBJECT,
    }

    json_type = node.get("type")
    gem_type = type_map.get(json_type, types.Type.STRING)

    schema_kwargs = {"type": gem_type}

    if json_type == "array" and "items" in node:
        schema_kwargs["items"] = json_to_gemini_schema(node["items"])

    if json_type == "object":
        properties = node.get("properties", {})
        schema_kwargs["properties"] = {
            k: json_to_gemini_schema(v) for k, v in properties.items()
        }
        schema_kwargs["required"] = node.get("required", [])

    return types.Schema(**schema_kwargs)
