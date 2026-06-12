"""CSV parser — encoding detection, delimiter sniffing, type inference, and preview.

Parses CSV file bytes into structured column metadata and sample rows
for the UI preview and later mapping configuration.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import datetime

from charset_normalizer import from_bytes

from app.core.logging import get_logger

logger = get_logger(__name__)

# Maximum rows to include in the preview
DEFAULT_PREVIEW_ROWS = 50

# Sample size for encoding and delimiter detection
SNIFF_SAMPLE_SIZE = 65_536  # 64 KB


@dataclass
class ColumnInfo:
    """Metadata for a single CSV column."""

    name: str
    inferred_type: str  # "string", "number", "date", "boolean"
    sample_values: list[str] = field(default_factory=list)
    null_count: int = 0
    total_count: int = 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "inferred_type": self.inferred_type,
            "sample_values": self.sample_values[:5],
            "null_count": self.null_count,
            "total_count": self.total_count,
        }


@dataclass
class CsvPreviewResult:
    """Result of parsing a CSV file for preview."""

    columns: list[ColumnInfo]
    preview_rows: list[dict[str, str]]
    total_rows: int
    encoding: str
    delimiter: str

    def to_dict(self) -> dict:
        return {
            "columns": [c.to_dict() for c in self.columns],
            "preview_rows": self.preview_rows,
            "total_rows": self.total_rows,
            "encoding": self.encoding,
            "delimiter": self.delimiter,
        }


# ── Type inference helpers ──

_BOOLEAN_VALUES = {"true", "false", "yes", "no", "evet", "hayır", "1", "0"}

_DATE_PATTERNS = [
    r"^\d{4}-\d{2}-\d{2}$",                          # 2024-01-15
    r"^\d{2}/\d{2}/\d{4}$",                           # 01/15/2024
    r"^\d{2}\.\d{2}\.\d{4}$",                         # 15.01.2024
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",         # ISO 8601
    r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$",        # 2024-01-15 10:30:00
]

_DATE_REGEXES = [re.compile(p) for p in _DATE_PATTERNS]


def _is_number(value: str) -> bool:
    """Check if a string looks like a number."""
    try:
        float(value.replace(",", "."))
        return True
    except (ValueError, AttributeError):
        return False


def _is_date(value: str) -> bool:
    """Check if a string matches common date patterns."""
    return any(r.match(value) for r in _DATE_REGEXES)


def _is_boolean(value: str) -> bool:
    """Check if a string is a boolean-like value."""
    return value.lower().strip() in _BOOLEAN_VALUES


def _infer_column_type(values: list[str]) -> str:
    """Infer the data type of a column from its non-empty values.

    Uses a voting strategy: if ≥80% of values match a type, use that type.
    Priority: boolean > date > number > string.
    """
    non_empty = [v.strip() for v in values if v.strip()]

    if not non_empty:
        return "string"

    total = len(non_empty)
    threshold = 0.8

    # Boolean check
    bool_count = sum(1 for v in non_empty if _is_boolean(v))
    if bool_count / total >= threshold:
        return "boolean"

    # Date check
    date_count = sum(1 for v in non_empty if _is_date(v))
    if date_count / total >= threshold:
        return "date"

    # Number check
    num_count = sum(1 for v in non_empty if _is_number(v))
    if num_count / total >= threshold:
        return "number"

    return "string"


def _detect_encoding(raw_bytes: bytes) -> str:
    """Detect the encoding of raw bytes using charset-normalizer.

    Falls back to utf-8 if detection fails.
    """
    result = from_bytes(raw_bytes[:SNIFF_SAMPLE_SIZE])
    best = result.best()

    if best is not None:
        encoding = best.encoding
        logger.info("Detected encoding: %s (confidence: %.2f)", encoding, best.coherence)
        return encoding

    logger.warning("Could not detect encoding, falling back to utf-8")
    return "utf-8"


def _detect_delimiter(text_sample: str) -> str:
    """Detect the CSV delimiter using csv.Sniffer.

    Falls back to comma if detection fails.
    """
    try:
        dialect = csv.Sniffer().sniff(text_sample, delimiters=",;\t|")
        logger.info("Detected delimiter: %r", dialect.delimiter)
        return dialect.delimiter
    except csv.Error:
        logger.warning("Could not detect delimiter, falling back to comma")
        return ","


def parse_csv_preview(
    file_bytes: bytes,
    max_rows: int = DEFAULT_PREVIEW_ROWS,
) -> CsvPreviewResult:
    """Parse a CSV file and return column metadata and preview rows.

    Args:
        file_bytes: Raw bytes of the CSV file.
        max_rows: Maximum number of rows to include in the preview.

    Returns:
        CsvPreviewResult with column info, preview data, and file stats.

    Raises:
        ValueError: If the file is empty or has no valid headers.
    """
    if not file_bytes:
        raise ValueError("CSV dosyası boş.")

    # Step 1: Detect encoding
    encoding = _detect_encoding(file_bytes)

    # Step 2: Decode
    try:
        text = file_bytes.decode(encoding)
    except (UnicodeDecodeError, LookupError):
        # Fallback to utf-8 with error replacement
        text = file_bytes.decode("utf-8", errors="replace")
        encoding = "utf-8"

    # Step 3: Detect delimiter
    sample = text[:SNIFF_SAMPLE_SIZE]
    delimiter = _detect_delimiter(sample)

    # Step 4: Parse CSV
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

    if not reader.fieldnames:
        raise ValueError("CSV dosyasında başlık satırı bulunamadı.")

    # Clean up column names
    column_names = [name.strip() for name in reader.fieldnames if name and name.strip()]

    if not column_names:
        raise ValueError("CSV dosyasında geçerli sütun adı bulunamadı.")

    # Step 5: Read all rows (for type inference) but store only preview
    all_column_values: dict[str, list[str]] = {col: [] for col in column_names}
    preview_rows: list[dict[str, str]] = []
    total_rows = 0

    for row in reader:
        total_rows += 1

        # Collect values for type inference
        for col in column_names:
            val = (row.get(col) or "").strip()
            all_column_values[col].append(val)

        # Store preview rows
        if total_rows <= max_rows:
            clean_row = {col: (row.get(col) or "").strip() for col in column_names}
            preview_rows.append(clean_row)

    # Step 6: Build column metadata
    columns: list[ColumnInfo] = []
    for col_name in column_names:
        values = all_column_values[col_name]
        null_count = sum(1 for v in values if not v)
        sample_values = [v for v in values if v][:5]

        col_info = ColumnInfo(
            name=col_name,
            inferred_type=_infer_column_type(values),
            sample_values=sample_values,
            null_count=null_count,
            total_count=total_rows,
        )
        columns.append(col_info)

    logger.info(
        "CSV parsed: %d columns, %d rows (preview: %d)",
        len(columns), total_rows, len(preview_rows),
    )

    return CsvPreviewResult(
        columns=columns,
        preview_rows=preview_rows,
        total_rows=total_rows,
        encoding=encoding,
        delimiter=delimiter,
    )
