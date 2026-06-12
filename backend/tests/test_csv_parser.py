"""Tests for the CSV parser — encoding, delimiter, type inference, edge cases."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.ingestion.csv_parser import (
    ColumnInfo,
    CsvPreviewResult,
    _infer_column_type,
    _is_boolean,
    _is_date,
    _is_number,
    parse_csv_preview,
)

FIXTURES = Path(__file__).parent / "fixtures"


class TestTypeInferenceHelpers:
    """Test individual type detection functions."""

    def test_is_number_integer(self) -> None:
        assert _is_number("42") is True

    def test_is_number_float(self) -> None:
        assert _is_number("3.14") is True

    def test_is_number_comma_decimal(self) -> None:
        assert _is_number("75,5") is True

    def test_is_number_negative(self) -> None:
        assert _is_number("-10") is True

    def test_is_number_string(self) -> None:
        assert _is_number("hello") is False

    def test_is_date_iso(self) -> None:
        assert _is_date("2024-01-15") is True

    def test_is_date_slash(self) -> None:
        assert _is_date("01/15/2024") is True

    def test_is_date_dot(self) -> None:
        assert _is_date("15.01.2024") is True

    def test_is_date_iso_datetime(self) -> None:
        assert _is_date("2024-01-15T10:30:00") is True

    def test_is_date_not_date(self) -> None:
        assert _is_date("not-a-date") is False

    def test_is_boolean_true(self) -> None:
        assert _is_boolean("true") is True
        assert _is_boolean("True") is True

    def test_is_boolean_false(self) -> None:
        assert _is_boolean("false") is True

    def test_is_boolean_yes_no(self) -> None:
        assert _is_boolean("yes") is True
        assert _is_boolean("no") is True

    def test_is_boolean_turkish(self) -> None:
        assert _is_boolean("evet") is True
        assert _is_boolean("hayır") is True

    def test_is_boolean_not_boolean(self) -> None:
        assert _is_boolean("maybe") is False


class TestColumnTypeInference:
    """Test the voting-based type inference."""

    def test_infer_number(self) -> None:
        values = ["1", "2.5", "3", "4.0", "5"]
        assert _infer_column_type(values) == "number"

    def test_infer_date(self) -> None:
        values = ["2024-01-01", "2024-02-15", "2024-03-30", "2024-04-10"]
        assert _infer_column_type(values) == "date"

    def test_infer_boolean(self) -> None:
        values = ["true", "false", "true", "true", "false"]
        assert _infer_column_type(values) == "boolean"

    def test_infer_string(self) -> None:
        values = ["hello", "world", "foo", "bar"]
        assert _infer_column_type(values) == "string"

    def test_infer_mixed_defaults_to_string(self) -> None:
        values = ["hello", "42", "2024-01-01", "true"]
        assert _infer_column_type(values) == "string"

    def test_infer_empty_is_string(self) -> None:
        assert _infer_column_type([]) == "string"

    def test_infer_all_empty_is_string(self) -> None:
        assert _infer_column_type(["", "", ""]) == "string"


class TestParseSimpleCsv:
    """Test parsing the simple comma-separated CSV fixture."""

    @pytest.fixture
    def result(self) -> CsvPreviewResult:
        content = (FIXTURES / "simple.csv").read_bytes()
        return parse_csv_preview(content)

    def test_column_count(self, result: CsvPreviewResult) -> None:
        assert len(result.columns) == 8

    def test_column_names(self, result: CsvPreviewResult) -> None:
        names = [c.name for c in result.columns]
        assert "patient_id" in names
        assert "first_name" in names
        assert "birth_date" in names
        assert "weight_kg" in names
        assert "is_active" in names

    def test_row_count(self, result: CsvPreviewResult) -> None:
        assert result.total_rows == 10

    def test_preview_rows(self, result: CsvPreviewResult) -> None:
        assert len(result.preview_rows) == 10  # all fit in preview

    def test_delimiter(self, result: CsvPreviewResult) -> None:
        assert result.delimiter == ","

    def test_type_inference_date(self, result: CsvPreviewResult) -> None:
        birth_col = next(c for c in result.columns if c.name == "birth_date")
        assert birth_col.inferred_type == "date"

    def test_type_inference_number(self, result: CsvPreviewResult) -> None:
        weight_col = next(c for c in result.columns if c.name == "weight_kg")
        assert weight_col.inferred_type == "number"

    def test_type_inference_boolean(self, result: CsvPreviewResult) -> None:
        active_col = next(c for c in result.columns if c.name == "is_active")
        assert active_col.inferred_type == "boolean"

    def test_type_inference_string(self, result: CsvPreviewResult) -> None:
        name_col = next(c for c in result.columns if c.name == "first_name")
        assert name_col.inferred_type == "string"

    def test_sample_values(self, result: CsvPreviewResult) -> None:
        name_col = next(c for c in result.columns if c.name == "first_name")
        assert len(name_col.sample_values) <= 5
        assert "Ahmet" in name_col.sample_values

    def test_null_count_zero(self, result: CsvPreviewResult) -> None:
        for col in result.columns:
            assert col.null_count == 0


class TestParseSemicolonCsv:
    """Test parsing semicolon-delimited CSV."""

    @pytest.fixture
    def result(self) -> CsvPreviewResult:
        content = (FIXTURES / "semicolon.csv").read_bytes()
        return parse_csv_preview(content)

    def test_delimiter(self, result: CsvPreviewResult) -> None:
        assert result.delimiter == ";"

    def test_column_count(self, result: CsvPreviewResult) -> None:
        assert len(result.columns) == 6

    def test_row_count(self, result: CsvPreviewResult) -> None:
        assert result.total_rows == 5


class TestParseLatin1Csv:
    """Test parsing Latin-1 encoded CSV."""

    @pytest.fixture
    def result(self) -> CsvPreviewResult:
        content = (FIXTURES / "latin1.csv").read_bytes()
        return parse_csv_preview(content)

    def test_column_count(self, result: CsvPreviewResult) -> None:
        assert len(result.columns) == 4

    def test_row_count(self, result: CsvPreviewResult) -> None:
        assert result.total_rows == 3


class TestParseLargeHeaderCsv:
    """Test parsing CSV with 50 columns."""

    @pytest.fixture
    def result(self) -> CsvPreviewResult:
        content = (FIXTURES / "large_header.csv").read_bytes()
        return parse_csv_preview(content)

    def test_column_count(self, result: CsvPreviewResult) -> None:
        assert len(result.columns) == 50

    def test_row_count(self, result: CsvPreviewResult) -> None:
        assert result.total_rows == 1


class TestEdgeCases:
    """Test error handling and edge cases."""

    def test_empty_file(self) -> None:
        with pytest.raises(ValueError, match="boş"):
            parse_csv_preview(b"")

    def test_header_only(self) -> None:
        content = b"col1,col2,col3\n"
        result = parse_csv_preview(content)
        assert len(result.columns) == 3
        assert result.total_rows == 0

    def test_max_rows_limit(self) -> None:
        # Create a CSV with more rows than max_rows
        lines = ["id,value"] + [f"{i},{i*10}" for i in range(100)]
        content = "\n".join(lines).encode("utf-8")
        result = parse_csv_preview(content, max_rows=5)
        assert len(result.preview_rows) == 5
        assert result.total_rows == 100

    def test_to_dict(self) -> None:
        content = b"name,age\nAlice,30\nBob,25\n"
        result = parse_csv_preview(content)
        d = result.to_dict()
        assert "columns" in d
        assert "preview_rows" in d
        assert "total_rows" in d
        assert d["total_rows"] == 2
