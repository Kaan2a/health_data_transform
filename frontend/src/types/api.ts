/**
 * TypeScript interfaces matching backend Pydantic schemas.
 *
 * These types are the frontend's source of truth for API data shapes.
 * In later sprints, these can be auto-generated from the OpenAPI spec.
 */

// ── Auth ──

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  organization_name?: string;
  organization_id?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  id: string;
  email: string;
  role: "owner" | "admin" | "viewer";
  organization_id: string;
}

// ── Projects ──

export type FhirResourceType = "Patient" | "Observation";

export interface ProjectCreate {
  name: string;
  resource_type: FhirResourceType;
  description?: string;
  fhir_version?: string;
}

export interface ProjectResponse {
  id: string;
  name: string;
  fhir_version: string;
  resource_type: FhirResourceType;
  description: string | null;
  organization_id: string;
  created_at: string;
  updated_at: string;
}

// ── Data Sources ──

export type DataSourceType = "csv" | "api";

export type DataSourceStatus =
  | "pending"
  | "uploaded"
  | "previewed"
  | "ready"
  | "error";

export interface DataSourceCreate {
  name: string;
  type: DataSourceType;
  api_url?: string;
  api_method?: string;
  api_headers?: Record<string, string>;
}

export interface DataSourceResponse {
  id: string;
  project_id: string;
  organization_id: string;
  name: string;
  type: DataSourceType;
  status: DataSourceStatus;

  // CSV fields
  file_path: string | null;
  file_name: string | null;
  file_size_bytes: number | null;
  row_count: number | null;

  // API fields
  api_url: string | null;
  api_method: string | null;
  api_headers: Record<string, string> | null;

  // Column metadata
  columns: ColumnInfo[] | null;
  preview_data: Record<string, string>[] | null;

  // Error
  error_message: string | null;

  // Timestamps
  created_at: string;
  updated_at: string;
}

export interface ColumnInfo {
  name: string;
  inferred_type: string;
  sample_values: string[];
  null_count: number;
  total_count: number;
}

export interface CsvPreviewResponse {
  columns: ColumnInfo[];
  preview_rows: Record<string, string>[];
  total_rows: number;
  encoding: string;
  delimiter: string;
}

export interface UploadResponse {
  file_name: string;
  file_size_bytes: number;
  status: DataSourceStatus;
}

// ── Common ──

export interface ApiSuccess<T> {
  data: T;
  requestId: string;
}

export interface ApiErrorBody {
  code: string;
  message: string;
  details: Array<{
    field?: string;
    message: string;
    code?: string;
  }>;
}

export interface ApiErrorResponse {
  error: ApiErrorBody;
  requestId: string;
}
