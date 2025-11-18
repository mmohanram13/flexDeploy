/**
 * API client for FlexDeploy backend
 */

const API_BASE_URL = 'http://localhost:8000/api';

class ApiClient {
  async get(endpoint) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        signal: AbortSignal.timeout(10000), // 10 second timeout
      });
      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }
      return response.json();
    } catch (error) {
      if (error.name === 'TimeoutError' || error.message.includes('fetch')) {
        throw new Error('Server not reachable. Please check if the server is running.');
      }
      throw error;
    }
  }

  async post(endpoint, data = {}) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
        signal: AbortSignal.timeout(30000), // 30 second timeout for AI operations
      });
      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }
      return response.json();
    } catch (error) {
      if (error.name === 'TimeoutError' || error.message.includes('fetch')) {
        throw new Error('Server not reachable. Please check if the server is running.');
      }
      throw error;
    }
  }

  async put(endpoint, data) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
        signal: AbortSignal.timeout(10000), // 10 second timeout
      });
      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }
      return response.json();
    } catch (error) {
      if (error.name === 'TimeoutError' || error.message.includes('fetch')) {
        throw new Error('Server not reachable. Please check if the server is running.');
      }
      throw error;
    }
  }

  async delete(endpoint) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'DELETE',
        signal: AbortSignal.timeout(10000), // 10 second timeout
      });
      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }
      return response.json();
    } catch (error) {
      if (error.name === 'TimeoutError' || error.message.includes('fetch')) {
        throw new Error('Server not reachable. Please check if the server is running.');
      }
      throw error;
    }
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

  async getDeploymentsStatus() {
    return this.get('/deployments/status/all');
  }

  async createDeployment(deploymentData) {
    return this.post('/deployments', deploymentData);
  }

  async runDeployment(deploymentId) {
    return this.post(`/deployments/${deploymentId}/run`);
  }

  async stopDeployment(deploymentId) {
    return this.post(`/deployments/${deploymentId}/stop`);
  }

  async deleteDeployment(deploymentId) {
    return this.delete(`/deployments/${deploymentId}`);
  }

  // Rings
  async getRings() {
    return this.get('/rings');
  }

  async updateRing(ringId, ringData) {
    return this.put(`/rings/${ringId}`, ringData);
  }

  // Gating Factors
  async getGatingFactors() {
    return this.get('/gating-factors');
  }

  async updateGatingFactors(gatingFactorsData) {
    return this.put('/gating-factors', gatingFactorsData);
  }

  // Dashboard
  async getDashboardMetrics() {
    return this.get('/dashboard/metrics');
  }

  async getDeviceDistribution() {
    return this.get('/dashboard/device-distribution');
  }

  // AI Agents
  async aiCategorizeDevices(deviceIds = null) {
    return this.post('/ai/categorize-devices', {
      deviceIds: deviceIds,
    });
  }

  async aiAnalyzeFailure(deploymentId, ringName) {
    return this.post('/ai/analyze-failure', {
      deploymentId: deploymentId,
      ringName: ringName,
    });
  }

  async aiParseGatingFactors(naturalLanguageInput) {
    return this.post('/ai/gating-factors', {
      naturalLanguageInput: naturalLanguageInput,
    });
  }

  async aiValidateGatingFactors(gatingFactors) {
    return this.post('/ai/validate-gating-factors', gatingFactors);
  }
}

export const apiClient = new ApiClient();
