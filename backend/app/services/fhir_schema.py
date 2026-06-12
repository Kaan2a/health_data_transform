"""FHIR Schema service — provides available paths for FHIR resources."""

from app.db.models.project import FhirResourceType


class FHIRSchemaService:
    """Service to get flattened FHIR paths for mapping."""

    # Simplified MVP schemas
    _SCHEMAS = {
        FhirResourceType.PATIENT: [
            {"path": "id", "type": "string", "description": "Logical id of this artifact"},
            {"path": "identifier[0].value", "type": "string", "description": "The value that is unique"},
            {"path": "active", "type": "boolean", "description": "Whether this patient's record is in active use"},
            {"path": "name[0].family", "type": "string", "description": "Family name (often called 'Surname')"},
            {"path": "name[0].given[0]", "type": "string", "description": "Given names (not always 'first'). Includes middle names"},
            {"path": "telecom[0].value", "type": "string", "description": "The actual contact point details"},
            {"path": "gender", "type": "string", "description": "male | female | other | unknown"},
            {"path": "birthDate", "type": "date", "description": "The date of birth for the individual"},
            {"path": "address[0].line[0]", "type": "string", "description": "Street name, number, direction & P.O. Box etc."},
            {"path": "address[0].city", "type": "string", "description": "Name of city, town etc."},
            {"path": "address[0].country", "type": "string", "description": "Country (e.g. can be ISO 3166 2 or 3 letter code)"},
        ],
        FhirResourceType.OBSERVATION: [
            {"path": "id", "type": "string", "description": "Logical id of this artifact"},
            {"path": "identifier[0].value", "type": "string", "description": "The value that is unique"},
            {"path": "status", "type": "string", "description": "registered | preliminary | final | amended +"},
            {"path": "category[0].coding[0].code", "type": "string", "description": "Classification of  type of observation"},
            {"path": "code.coding[0].code", "type": "string", "description": "Type of observation (code / type)"},
            {"path": "subject.reference", "type": "string", "description": "Who and/or what the observation is about (e.g. Patient/123)"},
            {"path": "effectiveDateTime", "type": "dateTime", "description": "Clinically relevant time/time-period for observation"},
            {"path": "valueQuantity.value", "type": "number", "description": "Numerical value (with implicit precision)"},
            {"path": "valueQuantity.unit", "type": "string", "description": "Unit representation"},
            {"path": "valueString", "type": "string", "description": "Actual result"},
        ],
    }

    @classmethod
    def get_schema(cls, resource_type: FhirResourceType) -> list[dict[str, str]]:
        """Get the available mapping paths for a FHIR resource type."""
        return cls._SCHEMAS.get(resource_type, [])
