import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Box,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material';
import {
  BugReport as BugIcon,
  Code as CodeIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { healrAPI } from '../services/api';

function Dashboard() {
  const [repoPath, setRepoPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStatistics();
  }, []);

  const loadStatistics = async () => {
    try {
      const response = await healrAPI.getLogStatistics();
      setStats(response.data.data);
    } catch (err) {
      console.error('Failed to load statistics:', err);
    }
  };

  const handleAnalyze = async () => {
    if (!repoPath) {
      setError('Please enter a repository path');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await healrAPI.analyzeRepository(repoPath);
      setAnalysis(response.data.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze repository');
    } finally {
      setLoading(false);
    }
  };

  const handleFix = async (dryRun = false) => {
    if (!repoPath) {
      setError('Please enter a repository path');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await healrAPI.fixRepository(repoPath, 'all', dryRun);
      alert(
        `${dryRun ? 'Dry run complete' : 'Fixes applied'}!\n` +
        `Fixes applied: ${response.data.data.fixes_applied}\n` +
        `Fixes failed: ${response.data.data.fixes_failed}`
      );
      await loadStatistics();
      if (!dryRun) {
        handleAnalyze();
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fix repository');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateTests = async () => {
    if (!repoPath) {
      setError('Please enter a repository path');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await healrAPI.generateTests(repoPath);
      alert(
        `Tests generated!\n` +
        `Total files: ${response.data.data.total_files || 1}\n` +
        `Success: ${response.data.data.success_count || (response.data.data.success ? 1 : 0)}`
      );
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate tests');
    } finally {
      setLoading(false);
    }
  };

  const prepareChartData = () => {
    if (!analysis || !analysis.issues) return [];

    return analysis.issues.slice(0, 10).map((item) => ({
      file: item.file.split('/').pop(),
      issues: item.issues.length,
      complexity: item.metrics.avg_complexity || 0,
      maintainability: item.metrics.avg_maintainability || 0,
    }));
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" gutterBottom>
        Healr Dashboard
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        AI-Powered Code Self-Healing System
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mt: 2, mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3} sx={{ mt: 2 }}>
        {/* Statistics Cards */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <div>
                  <Typography color="text.secondary" gutterBottom>
                    Total Operations
                  </Typography>
                  <Typography variant="h4">
                    {stats?.total_operations || 0}
                  </Typography>
                </div>
                <CodeIcon color="primary" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <div>
                  <Typography color="text.secondary" gutterBottom>
                    Successful Fixes
                  </Typography>
                  <Typography variant="h4" color="success.main">
                    {stats?.successful_operations || 0}
                  </Typography>
                </div>
                <CheckIcon color="success" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <div>
                  <Typography color="text.secondary" gutterBottom>
                    Failed Operations
                  </Typography>
                  <Typography variant="h4" color="error.main">
                    {stats?.failed_operations || 0}
                  </Typography>
                </div>
                <ErrorIcon color="error" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <div>
                  <Typography color="text.secondary" gutterBottom>
                    Files Modified
                  </Typography>
                  <Typography variant="h4">
                    {stats?.files_modified_count || 0}
                  </Typography>
                </div>
                <BugIcon color="warning" sx={{ fontSize: 40 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Analysis Section */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                Analyze Repository
              </Typography>
              <Box display="flex" gap={2} mt={2}>
                <TextField
                  fullWidth
                  label="Repository Path"
                  value={repoPath}
                  onChange={(e) => setRepoPath(e.target.value)}
                  placeholder="/path/to/your/repository"
                  disabled={loading}
                />
                <Button
                  variant="contained"
                  onClick={handleAnalyze}
                  disabled={loading}
                  sx={{ minWidth: 120 }}
                >
                  {loading ? <CircularProgress size={24} /> : 'Analyze'}
                </Button>
              </Box>

              {analysis && (
                <Box mt={3}>
                  <Typography variant="h6" gutterBottom>
                    Analysis Results
                  </Typography>
                  <Box display="flex" gap={2} mt={2} mb={2}>
                    <Chip label={`Files: ${analysis.files_analyzed}`} color="primary" />
                    <Chip label={`Issues: ${analysis.total_issues}`} color="warning" />
                    <Chip label={`Files with Issues: ${analysis.files_with_issues}`} color="error" />
                  </Box>

                  <Box display="flex" gap={2} mt={2}>
                    <Button
                      variant="contained"
                      color="success"
                      onClick={() => handleFix(false)}
                      disabled={loading || analysis.total_issues === 0}
                    >
                      Apply Fixes
                    </Button>
                    <Button
                      variant="outlined"
                      onClick={() => handleFix(true)}
                      disabled={loading || analysis.total_issues === 0}
                    >
                      Dry Run
                    </Button>
                    <Button
                      variant="outlined"
                      color="secondary"
                      onClick={handleGenerateTests}
                      disabled={loading}
                    >
                      Generate Tests
                    </Button>
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Chart */}
        {analysis && analysis.issues.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Issues by File
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={prepareChartData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="file" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="issues" fill="#ff9800" name="Issues" />
                    <Bar dataKey="complexity" fill="#f44336" name="Complexity" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Container>
  );
}

export default Dashboard;
