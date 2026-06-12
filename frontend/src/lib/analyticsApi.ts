import { api } from "./api";

export interface DashboardStats {
  total_projects: number;
  total_jobs: number;
  total_rows_processed: number;
  total_rows_success: number;
  total_rows_failed: number;
}

export const analyticsApi = {
  getDashboardStats: async () => {
    const res = await api.get<DashboardStats>("/api/v1/analytics/dashboard");
    return res.data;
  },
};
