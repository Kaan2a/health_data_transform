export type TransformationType = "direct" | "date_format" | "concat" | "lookup" | "custom_script";

export interface TransformationConfig {
  format?: string; // For date_format
  separator?: string; // For concat
  lookupTable?: Record<string, string>; // For lookup
  script?: string; // For custom_script
  [key: string]: any;
}

export interface MappingRule {
  id: string;
  projectId: string;
  organizationId: string;
  dataSourceId: string;
  sourceField: string;
  targetFhirField: string;
  transformationType: TransformationType;
  transformationConfig?: TransformationConfig | null;
  valueMap?: Record<string, string> | null;
  createdAt: string;
  updatedAt: string;
}

export interface MappingRuleCreate {
  source_field: string;
  target_fhir_field: string;
  transformation_type: TransformationType;
  transformation_config?: TransformationConfig | null;
  value_map?: Record<string, string> | null;
}

export interface FhirSchemaField {
  path: string;
  type: string;
  description: string;
}

export interface AutoMapRequest {
  columns: string[];
}

export interface BatchMappingRequest {
  rules: MappingRuleCreate[];
}
