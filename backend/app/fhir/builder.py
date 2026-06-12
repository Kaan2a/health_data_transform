"""FHIR resource builder from data records and mapping rules."""

import datetime
from typing import Any

from app.db.models.mapping import MappingRule


def apply_transformation(value: Any, rule: MappingRule) -> Any:
    """Applies a transformation rule to a source value."""
    if value is None or str(value).strip() == "":
        return None

    t_type = rule.transformation_type
    config = rule.transformation_config or {}

    if rule.value_map and isinstance(rule.value_map, dict):
        val_str = str(value).strip()
        if val_str in rule.value_map:
            value = rule.value_map[val_str]

    try:
        if t_type == "direct":
            return value
        elif t_type == "date_format":
            fmt = config.get("format", "%Y-%m-%d")
            # Parse from the given format
            parsed = datetime.datetime.strptime(str(value).strip(), fmt)
            # Output in standard FHIR format (YYYY-MM-DD)
            return parsed.strftime("%Y-%m-%d")
        elif t_type == "lookup":
            lookup_table = config.get("lookupTable", {})
            return lookup_table.get(str(value).strip(), str(value))
        elif t_type == "concat":
            # For MVP, concat works with single column stringification
            return str(value)
        elif t_type == "custom_script":
            # Unsafe for MVP to run eval, return direct
            return value
        else:
            return value
    except Exception as e:
        raise ValueError(f"Transformation '{t_type}' failed for value '{value}': {str(e)}")


def set_nested_value(d: dict, path: str, value: Any) -> None:
    """
    Sets a value in a nested dictionary using a JSON-like path.
    Example paths: 'name[0].family', 'identifier[0].value', 'birthDate'
    """
    if value is None:
        return

    parts = path.split('.')
    current = d
    for i, part in enumerate(parts[:-1]):
        if '[' in part and part.endswith(']'):
            key, idx_str = part[:-1].split('[')
            idx = int(idx_str)
            if key not in current:
                current[key] = []
            while len(current[key]) <= idx:
                current[key].append({})
            current = current[key][idx]
        else:
            if part not in current:
                current[part] = {}
            current = current[part]

    last_part = parts[-1]
    if '[' in last_part and last_part.endswith(']'):
        key, idx_str = last_part[:-1].split('[')
        idx = int(idx_str)
        if key not in current:
            current[key] = []
        while len(current[key]) <= idx:
            current[key].append(None)
        current[key][idx] = value
    else:
        current[last_part] = value


def build_fhir_resource(resource_type: str, row: dict[str, Any], rules: list[MappingRule]) -> dict[str, Any]:
    """
    Build a complete FHIR resource from a source data row.
    Raises ValueError if a transformation fails.
    """
    resource: dict[str, Any] = {"resourceType": resource_type}

    for rule in rules:
        val = row.get(rule.source_field)
        if val is not None and str(val).strip() != "":
            # Will raise ValueError if transformation fails
            transformed_val = apply_transformation(val, rule)
            if transformed_val is not None:
                set_nested_value(resource, rule.target_fhir_field, transformed_val)

    # Validate using fhir.resources
    try:
        from fhir.resources import get_fhir_model_class
        model_class = get_fhir_model_class(resource_type)
        # Pydantic v2 validation
        model_obj = model_class.model_validate(resource)
        # Return the validated JSON dictionary
        return model_obj.model_dump(exclude_none=True, mode="json")
    except Exception as e:
        raise ValueError(f"FHIR Schema Validation Error: {str(e)}")

