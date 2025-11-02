/**
 * API client for FlexDeploy backend
 */

const API_BASE_URL = 'http://localhost:8000/api';

class ApiClient {
  async get(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    return response.json();
  }

  async post(endpoint, data = {}) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    return response.json();
  }

  async put(endpoint, data) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }
    return response.json();
  }

  // Devices
  async getDevices() {
    return this.get('/devices');
  }

  // Deployments
  async getDeployments() {
    return this.get('/deployments');
  }

  async getDeploymentDetail(deploymentId) {
    return this.get(`/deployments/${deploymentId}`);
  }

  async runDeployment(deploymentId) {
    return this.post(`/deployments/${deploymentId}/run`);
  }

  async stopDeployment(deploymentId) {
    return this.post(`/deployments/${deploymentId}/stop`);
  }

  // Rings
  async getRings() {
    return this.get('/rings');
  }

  async updateRing(ringId, ringData) {
    return this.put(`/rings/${ringId}`, ringData);
  }

  // Dashboard
  async getDashboardMetrics() {
    return this.get('/dashboard/metrics');
  }

  async getDeviceDistribution() {
    return this.get('/dashboard/device-distribution');
  }
}

export const apiClient = new ApiClient();
