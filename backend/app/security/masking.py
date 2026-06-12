import hashlib
from enum import Enum
from typing import Any

class MaskingType(str, Enum):
    NONE = "NONE"
    HASH = "HASH"
    REDACT = "REDACT"
    PARTIAL = "PARTIAL"

def apply_mask(value: Any, masking_type: MaskingType) -> Any:
    """
    Applies the chosen masking strategy to the given value.
    """
    if not value or masking_type == MaskingType.NONE:
        return value
        
    val_str = str(value)

    if masking_type == MaskingType.REDACT:
        return "***"
    
    elif masking_type == MaskingType.HASH:
        # Return SHA-256 hash
        return hashlib.sha256(val_str.encode("utf-8")).hexdigest()
    
    elif masking_type == MaskingType.PARTIAL:
        # If length is small, just redact completely
        if len(val_str) <= 2:
            return "***"
        # Keep first 2 characters, mask the rest
        return val_str[:2] + "***"
    
    return value
