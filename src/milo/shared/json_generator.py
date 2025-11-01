import json
from typing import List, Dict, Any, Union, Optional
from datetime import datetime, date
from enum import Enum
from sqlmodel import SQLModel
from pydantic import BaseModel


def jsonify_value(value: Any) -> Any:
    """
    Recursively convert a value to a JSON-serializable format.

    Handles:
    - Enum objects -> their string values
    - datetime objects -> ISO format strings
    - date objects -> ISO format strings
    - SQLModel/Pydantic models -> dictionaries
    - Lists/Tuples -> lists with converted values
    - Dictionaries -> dictionaries with converted values
    - Already serialized values -> unchanged

    Args:
        value: Value to convert

    Returns:
        JSON-serializable equivalent
    """
    if value is None:
        return None

    # Handle Enum types
    if isinstance(value, Enum):
        return value.value

    # Handle datetime objects
    if isinstance(value, datetime):
        return value.isoformat()

    # Handle date objects
    if isinstance(value, date):
        return value.isoformat()

    # Handle SQLModel instances
    if isinstance(value, SQLModel):
        return jsonify_model(value)

    # Handle Pydantic BaseModel instances
    if isinstance(value, BaseModel):
        return jsonify_model(value)

    # Handle lists and tuples
    if isinstance(value, (list, tuple)):
        return [jsonify_value(item) for item in value]

    # Handle dictionaries
    if isinstance(value, dict):
        return {key: jsonify_value(val) for key, val in value.items()}

    # For primitive types (str, int, float, bool), return as-is
    return value


def jsonify_model(model: Union[SQLModel, BaseModel]) -> Dict[str, Any]:
    """
    Convert a SQLModel or Pydantic model to a JSON-serializable dictionary.

    Args:
        model: SQLModel or Pydantic model instance

    Returns:
        Dictionary with all model fields converted to JSON-serializable types
    """
    if isinstance(model, SQLModel):
        # Use model_dump() for SQLModel (SQLModel extends Pydantic)
        model_dict = model.model_dump() if hasattr(model, "model_dump") else dict(model)
    elif isinstance(model, BaseModel):
        model_dict = model.model_dump()
    else:
        # Fallback: convert to dict using __dict__
        model_dict = dict(model) if hasattr(model, "__dict__") else {}

    # Recursively convert all values
    return {key: jsonify_value(val) for key, val in model_dict.items()}


def jsonify(
    obj: Union[List[Any], Any],
) -> Union[List[Dict[str, Any]], Dict[str, Any], Any]:
    """
    Universal function to convert one or more objects to JSON-serializable format.

    Works with:
    - Single SQLModel/Pydantic objects
    - Lists of SQLModel/Pydantic objects
    - Dictionaries (recursively converted)
    - Primitive types

    Args:
        obj: Object(s) to serialize

    Returns:
        JSON-serializable representation
    """
    # Handle lists
    if isinstance(obj, list):
        return [jsonify_value(item) for item in obj]

    # Handle single object
    if isinstance(obj, (SQLModel, BaseModel)):
        return jsonify_model(obj)

    # Handle dictionaries
    if isinstance(obj, dict):
        return jsonify_value(obj)

    # Handle single values
    return jsonify_value(obj)


def to_json_string(
    obj: Union[List[Any], Any], indent: int = 2, ensure_ascii: bool = False
) -> str:
    """
    Convert objects to a JSON string.

    Args:
        obj: Object(s) to serialize
        indent: JSON indentation level (default: 2, None for compact)
        ensure_ascii: If True, escape non-ASCII characters (default: False)

    Returns:
        JSON string representation
    """
    data = jsonify(obj)
    return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
