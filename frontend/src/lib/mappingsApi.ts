import { api } from "./api";
import type {
  AutoMapRequest,
  BatchMappingRequest,
  FhirSchemaField,
  MappingRuleCreate,
  MappingRule,
} from "../types/mapping";

export const mappingsApi = {
  getFhirSchema: async (projectId: string) => {
    return api.get<FhirSchemaField[]>(`/api/v1/projects/${projectId}/fhir-schema`);
  },

  listMappingRules: async (projectId: string, sourceId: string) => {
    return api.get<MappingRule[]>(
      `/api/v1/projects/${projectId}/sources/${sourceId}/mappings`
    );
  },

  batchUpdateMappings: async (
    projectId: string,
    sourceId: string,
    request: BatchMappingRequest
  ) => {
    return api.post<MappingRule[]>(
      `/api/v1/projects/${projectId}/sources/${sourceId}/mappings/batch`,
      request
    );
  },

  autoSuggestMappings: async (
    projectId: string,
    sourceId: string,
    request: AutoMapRequest
  ) => {
    return api.post<MappingRuleCreate[]>(
      `/api/v1/projects/${projectId}/sources/${sourceId}/mappings/auto-suggest`,
      request
    );
  },

  previewMappings: async (projectId: string, sourceId: string) => {
    return api.post<any[]>(
      `/api/v1/projects/${projectId}/sources/${sourceId}/mappings/preview`
    );
  },
};
