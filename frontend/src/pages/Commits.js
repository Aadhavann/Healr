import React, { useState } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Box,
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent,
  Alert,
} from '@mui/material';
import { CommitOutlined as CommitIcon } from '@mui/icons-material';
import { healrAPI } from '../services/api';

function Commits() {
  const [repoPath, setRepoPath] = useState('');
  const [commits, setCommits] = useState([]);
  const [error, setError] = useState(null);

  const loadCommits = async () => {
    if (!repoPath) {
      setError('Please enter a repository path');
      return;
    }

    setError(null);

    try {
      const response = await healrAPI.getCommits(repoPath, 20);
      setCommits(response.data.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load commits');
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString();
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" gutterBottom>
        Commit History
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" gap={2}>
            <TextField
              fullWidth
              label="Repository Path"
              value={repoPath}
              onChange={(e) => setRepoPath(e.target.value)}
              placeholder="/path/to/your/repository"
            />
            <Button variant="contained" onClick={loadCommits} sx={{ minWidth: 120 }}>
              Load Commits
            </Button>
          </Box>
        </CardContent>
      </Card>

      {commits.length > 0 && (
        <Card>
          <CardContent>
            <Timeline position="alternate">
              {commits.map((commit, index) => (
                <TimelineItem key={commit.hash}>
                  <TimelineOppositeContent color="text.secondary">
                    <Typography variant="body2">
                      {formatTime(commit.date)}
                    </Typography>
                    <Typography variant="caption">
                      {formatDate(commit.date).split(',')[0]}
                    </Typography>
                  </TimelineOppositeContent>
                  <TimelineSeparator>
                    <TimelineDot color="primary">
                      <CommitIcon />
                    </TimelineDot>
                    {index < commits.length - 1 && <TimelineConnector />}
                  </TimelineSeparator>
                  <TimelineContent>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="subtitle2" color="primary">
                          {commit.short_hash}
                        </Typography>
                        <Typography variant="body1" sx={{ mt: 1 }}>
                          {commit.message.split('\n')[0]}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                          by {commit.author}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {commit.files_changed} file(s) changed
                        </Typography>
                      </CardContent>
                    </Card>
                  </TimelineContent>
                </TimelineItem>
              ))}
            </Timeline>
          </CardContent>
        </Card>
      )}

      {commits.length === 0 && (
        <Box textAlign="center" py={4}>
          <Typography color="text.secondary">
            Enter a repository path and click "Load Commits" to view commit history
          </Typography>
        </Box>
      )}
    </Container>
  );
}

export default Commits;
