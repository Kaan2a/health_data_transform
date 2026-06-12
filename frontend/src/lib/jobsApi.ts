import { api } from "./api";

export interface JobIssue {
  id: string;
  job_id: string;
  row_index: number | null;
  issue_type: "warning" | "error";
  field_name: string | null;
  message: string;
}

export interface JobResponse {
  id: string;
  project_id: string;
  organization_id: string;
  data_source_id: string;
  status: "pending" | "running" | "completed" | "failed";
  total_rows: number;
  processed_rows: number;
  successful_rows: number;
  failed_rows: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export const jobsApi = {
  startJob: async (projectId: string, sourceId: string) => {
    const res = await api.post<JobResponse>(`/api/v1/projects/${projectId}/sources/${sourceId}/jobs`);
    return res.data;
  },
  
  getJobs: async (projectId: string) => {
    const res = await api.get<JobResponse[]>(`/api/v1/projects/${projectId}/jobs`);
    return res.data;
  },

  getJobStatus: async (projectId: string, jobId: string) => {
    const res = await api.get<JobResponse>(`/api/v1/projects/${projectId}/jobs/${jobId}`);
    return res.data;
  },

  getJobIssues: async (projectId: string, jobId: string) => {
    const res = await api.get<JobIssue[]>(`/api/v1/projects/${projectId}/jobs/${jobId}/issues`);
    return res.data;
  },

  getDownloadUrl: (projectId: string, jobId: string) => {
    // Return the full URL for downloading so we can use it in an <a href> directly
    return `http://localhost:8000/api/v1/projects/${projectId}/jobs/${jobId}/download`;
  },

  exportJob: async (projectId: string, jobId: string, data: any) => {
    const res = await api.post<any>(`/api/v1/jobs/export`, { project_id: projectId, job_id: jobId, ...data });
    return res.data;
  }
};
