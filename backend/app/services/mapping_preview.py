"""Mapping Preview service — generates sample FHIR JSON based on mapping rules."""

import re
from typing import Any

from app.db.models.mapping import MappingRule
from app.db.models.project import FhirResourceType


class MappingPreviewService:
    """Applies mapping rules to generate FHIR preview data."""

    @staticmethod
    def _set_nested_value(obj: dict[str, Any], path: str, value: Any) -> None:
        """Set a value in a nested dictionary/list structure using a path.

        Path example: 'name[0].family' or 'identifier[0].value'
        """
        parts = re.split(r'\.|\[|\]', path)
        parts = [p for p in parts if p]  # filter empty strings

        current: Any = obj
        for i, part in enumerate(parts):
            is_last = i == len(parts) - 1

            if is_last:
                if isinstance(current, list):
                    idx = int(part)
                    while len(current) <= idx:
                        current.append(None)
                    current[idx] = value
                else:
                    current[part] = value
                break

            # Look ahead to see if next part is an array index
            next_part_is_index = parts[i + 1].isdigit()

            if isinstance(current, list):
                idx = int(part)
                while len(current) <= idx:
                    current.append([] if next_part_is_index else {})
                if current[idx] is None:
                    current[idx] = [] if next_part_is_index else {}
                current = current[idx]
            else:
                if part not in current:
                    current[part] = [] if next_part_is_index else {}
                current = current[part]

    @classmethod
    def generate_preview(
        cls,
        preview_data: list[dict[str, Any]],
        rules: list[MappingRule],
        resource_type: FhirResourceType,
    ) -> list[dict[str, Any]]:
        """Generate FHIR resources from preview data."""
        results = []

        for row in preview_data:
            resource: dict[str, Any] = {
                "resourceType": resource_type.value,
            }

            for rule in rules:
                source_val = row.get(rule.source_field)
                if source_val is None or str(source_val).strip() == "":
                    continue

                # Apply transformations
                transformed_val = source_val
                if rule.transformation_type == "date_format" and rule.transformation_config:
                    # MVP: simply assume transformed_val is valid FHIR date format for now
                    # A robust implementation would parse source_val using config['format']
                    # and output YYYY-MM-DD
                    pass

                cls._set_nested_value(resource, rule.target_fhir_field, transformed_val)

            results.append(resource)

        return results
