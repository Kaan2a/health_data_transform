/**
 * API client — centralized HTTP wrapper with JWT interceptor.
 *
 * All backend requests go through this module to ensure:
 *  - Base URL configuration
 *  - JWT Bearer token injection
 *  - Standard error response parsing
 *  - Request ID forwarding
 */

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

interface ApiError {
  error: {
    code: string;
    message: string;
    details: Array<{ field?: string; message: string; code?: string }>;
  };
  requestId: string;
}

interface ApiSuccess<T> {
  data: T;
  requestId: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getHeaders(): HeadersInit {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    const token = localStorage.getItem("access_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorBody: ApiError = await response.json().catch(() => ({
        error: {
          code: "NETWORK_ERROR",
          message: "Sunucuya bağlanılamadı.",
          details: [],
        },
        requestId: "",
      }));
      throw new ApiRequestError(
        errorBody.error.message,
        errorBody.error.code,
        response.status,
        errorBody.error.details
      );
    }
    const json = await response.json();
    // Wrap raw arrays or objects without 'data' field to match ApiSuccess interface
    if (json && typeof json === "object" && "data" in json) {
      return json;
    }
    return { data: json, requestId: "" } as unknown as T;
  }

  async get<T>(path: string): Promise<ApiSuccess<T>> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "GET",
      headers: this.getHeaders(),
    });
    return this.handleResponse<ApiSuccess<T>>(response);
  }

  async post<T>(path: string, body?: unknown): Promise<ApiSuccess<T>> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: this.getHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    });
    return this.handleResponse<ApiSuccess<T>>(response);
  }

  async put<T>(path: string, body?: unknown): Promise<ApiSuccess<T>> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "PUT",
      headers: this.getHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    });
    return this.handleResponse<ApiSuccess<T>>(response);
  }

  async delete<T>(path: string): Promise<ApiSuccess<T>> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "DELETE",
      headers: this.getHeaders(),
    });
    return this.handleResponse<ApiSuccess<T>>(response);
  }

  async upload<T>(path: string, formData: FormData): Promise<ApiSuccess<T>> {
    const headers: Record<string, string> = {};
    const token = localStorage.getItem("access_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    // Don't set Content-Type for FormData — browser sets it with boundary
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers,
      body: formData,
    });
    return this.handleResponse<ApiSuccess<T>>(response);
  }
}

export class ApiRequestError extends Error {
  code: string;
  statusCode: number;
  details: Array<{ field?: string; message: string; code?: string }>;

  constructor(
    message: string,
    code: string,
    statusCode: number,
    details: Array<{ field?: string; message: string; code?: string }> = []
  ) {
    super(message);
    this.name = "ApiRequestError";
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
  }
}

export const api = new ApiClient(API_BASE_URL);
