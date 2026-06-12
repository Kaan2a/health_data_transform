"""AutoMapper service — suggests mapping rules based on column names."""

import re
from typing import Any

from app.db.models.project import FhirResourceType


class AutoMapperService:
    """Provides mapping suggestions for CSV columns."""

    # Common synonyms mapped to standard FHIR paths
    _SYNONYMS = {
        FhirResourceType.PATIENT: {
            "name[0].family": ["soyadi", "soyad", "last_name", "lastname", "surname"],
            "name[0].given[0]": ["adi", "ad", "first_name", "firstname", "name", "isim"],
            "identifier[0].value": ["tc", "tckn", "tc_kimlik", "id", "kimlik", "passport", "hasta_no"],
            "gender": ["cinsiyet", "gender", "sex"],
            "birthDate": ["dogum_tarihi", "dob", "birthdate", "birth_date", "dtarihi", "dogum"],
            "telecom[0].value": ["telefon", "tel", "phone", "email", "eposta", "e-posta", "iletisim"],
            "address[0].city": ["sehir", "il", "city"],
            "address[0].country": ["ulke", "country"],
            "active": ["aktif", "durum", "active", "status"],
        },
        FhirResourceType.OBSERVATION: {
            "valueQuantity.value": ["deger", "sonuc", "value", "result", "miktar"],
            "valueQuantity.unit": ["birim", "unit"],
            "code.coding[0].code": ["test_kodu", "loinc", "kodu", "code", "islem_kodu"],
            "effectiveDateTime": ["tarih", "zaman", "date", "time", "islem_zamani", "kayit_tarihi"],
            "subject.reference": ["hasta_id", "patient_id", "tc"],
            "status": ["durum", "status"],
        },
    }

    @classmethod
    def suggest_mappings(
        cls, columns: list[str], resource_type: FhirResourceType
    ) -> list[dict[str, Any]]:
        """Suggest mapping rules for a list of column names."""
        suggestions = []
        synonyms = cls._SYNONYMS.get(resource_type, {})

        # Build reverse lookup: lowercase_synonym -> fhir_path
        reverse_lookup = {}
        for fhir_path, syn_list in synonyms.items():
            for syn in syn_list:
                reverse_lookup[syn] = fhir_path

        for col in columns:
            # Clean up column name for matching (remove spaces, underscores, etc.)
            clean_col = re.sub(r"[^a-z0-9]", "", col.lower())
            
            # Exact match attempt
            if clean_col in reverse_lookup:
                suggestions.append(
                    {
                        "source_field": col,
                        "target_fhir_field": reverse_lookup[clean_col],
                        "transformation_type": "direct",
                        "transformation_config": None,
                    }
                )
                continue

            # Partial match attempt
            matched = False
            for syn, fhir_path in reverse_lookup.items():
                if len(syn) > 3 and (syn in clean_col or clean_col in syn):
                    suggestions.append(
                        {
                            "source_field": col,
                            "target_fhir_field": fhir_path,
                            "transformation_type": "direct",
                            "transformation_config": None,
                        }
                    )
                    matched = True
                    break
            
            # If not matched, try date types to guess date formats
            if not matched and ("tarih" in clean_col or "date" in clean_col):
                # Suggest effectiveDateTime for Observation, or birthDate for Patient if not caught
                if resource_type == FhirResourceType.OBSERVATION:
                    suggestions.append(
                        {
                            "source_field": col,
                            "target_fhir_field": "effectiveDateTime",
                            "transformation_type": "direct",
                            "transformation_config": None,
                        }
                    )

        return suggestions
