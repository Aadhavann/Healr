import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API methods
export const healrAPI = {
  // Health check
  healthCheck: () => api.get('/health'),

  // Analysis
  analyzeRepository: (repoPath) =>
    api.post('/api/analyze', { repo_path: repoPath }),

  // Fix
  fixRepository: (repoPath, taskType = 'all', dryRun = false) =>
    api.post('/api/fix', {
      repo_path: repoPath,
      task_type: taskType,
      dry_run: dryRun,
    }),

  // Tests
  generateTests: (repoPath, filePath = null) =>
    api.post('/api/generate-tests', {
      repo_path: repoPath,
      file_path: filePath,
    }),

  // Logs
  getLogs: (operationType = null, filePath = null, limit = 100) =>
    api.get('/api/logs', {
      params: {
        operation_type: operationType,
        file_path: filePath,
        limit,
      },
    }),

  getLogStatistics: () => api.get('/api/logs/statistics'),

  searchLogs: (query) =>
    api.get('/api/logs/search', {
      params: { query },
    }),

  // Commits
  getCommits: (repoPath, maxCount = 10) =>
    api.get('/api/commits', {
      params: {
        repo_path: repoPath,
        max_count: maxCount,
      },
    }),

  getRepoStatus: (repoPath) =>
    api.get('/api/commits/status', {
      params: { repo_path: repoPath },
    }),

  // Metrics
  getMetrics: (repoPath) =>
    api.get('/api/metrics', {
      params: { repo_path: repoPath },
    }),

  // Config
  getConfig: () => api.get('/api/config'),

  updateConfig: (config) => api.post('/api/config', config),

  // Report
  generateReport: (repoPath) =>
    api.get('/api/report', {
      params: { repo_path: repoPath },
    }),
};

export default api;
