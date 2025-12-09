// API service for communicating with OmniVid-Lite backend
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface RenderRequest {
  prompt: string;
  creative?: boolean;
}

export interface RenderResponse {
  job_id: string;
  status: string;
  poll_url: string;
  download_url: string;
}

export interface JobStatus {
  job_id: string;
  status: string;
  progress: number;
  output_path?: string;
  error?: string;
  created_at: string;
  updated_at: string;
}

export interface JobSummary {
  job_id: string;
  status: string;
  output_path?: string;
  created_at: string;
  updated_at: string;
}

export interface JobListResponse {
  jobs: JobSummary[];
}

class ApiService {
  private apiKey: string = '';

  setApiKey(apiKey: string) {
    this.apiKey = apiKey;
  }

  private getHeaders() {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }
    return headers;
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const config: RequestInit = {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...options.headers,
      },
    };

    const response = await fetch(url, config);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Network error' }));
      throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  // Authentication
  async validateApiKey(apiKey: string): Promise<boolean> {
    try {
      this.apiKey = apiKey;
      await this.request('/api/v1/render/status/test');
      return true;
    } catch (error) {
      this.apiKey = '';
      return false;
    }
  }

  // Render operations
  async startRender(request: RenderRequest): Promise<RenderResponse> {
    return this.request<RenderResponse>('/api/v1/render', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getJobStatus(jobId: string): Promise<JobStatus> {
    return this.request<JobStatus>(`/api/v1/render/status/${jobId}`);
  }

  async listJobs(limit: number = 50): Promise<JobListResponse> {
    return this.request<JobListResponse>(`/api/v1/render/jobs?limit=${limit}`);
  }

  async downloadVideo(jobId: string): Promise<Blob> {
    const url = `${API_BASE_URL}/api/v1/render/download/${jobId}`;
    const response = await fetch(url, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Download failed: ${response.statusText}`);
    }

    return response.blob();
  }

  // Utility
  async checkHealth(): Promise<{ status: string }> {
    return this.request('/api/v1/health');
  }
}

export const apiService = new ApiService();