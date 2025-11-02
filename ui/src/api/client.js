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
        // Try to get detailed error message from response
        let errorMessage = `API error: ${response.statusText}`;
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            errorMessage = Array.isArray(errorData.detail) 
              ? errorData.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join(', ')
              : errorData.detail;
          }
        } catch (e) {
          // If we can't parse the error, use the default message
        }
        throw new Error(errorMessage);
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

  // Simulator APIs
  async createDevice(deviceData) {
    return this.post('/simulator/devices', deviceData);
  }

  async updateDeviceMetrics(metricsData) {
    return this.post('/simulator/device-metrics', metricsData);
  }

  async updateRingMetrics(ringMetricsData) {
    return this.post('/simulator/ring-metrics', ringMetricsData);
  }

  async updateDeploymentRingStatus(statusData) {
    return this.post('/simulator/deployment-status', statusData);
  }

  async getRingDevices(deploymentId, ringId) {
    return this.get(`/simulator/deployment/${deploymentId}/ring/${ringId}/devices`);
  }

  async reinitApplication() {
    return this.post('/simulator/reinit');
  }
}

export const apiClient = new ApiClient();
