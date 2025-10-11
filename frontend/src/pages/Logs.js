import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  TextField,
  Box,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Collapse,
} from '@mui/material';
import { ExpandMore as ExpandMoreIcon } from '@mui/icons-material';
import { healrAPI } from '../services/api';

function Logs() {
  const [logs, setLogs] = useState([]);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedLog, setExpandedLog] = useState(null);

  useEffect(() => {
    loadLogs();
  }, [filter]);

  const loadLogs = async () => {
    try {
      const response = await healrAPI.getLogs(
        filter === 'all' ? null : filter,
        null,
        100
      );
      setLogs(response.data.data);
    } catch (err) {
      console.error('Failed to load logs:', err);
    }
  };

  const handleSearch = async () => {
    if (!searchTerm) {
      loadLogs();
      return;
    }

    try {
      const response = await healrAPI.searchLogs(searchTerm);
      setLogs(response.data.data);
    } catch (err) {
      console.error('Search failed:', err);
    }
  };

  const getOperationColor = (opType) => {
    const colors = {
      issue_detection: 'info',
      llm_interaction: 'secondary',
      code_edit: 'warning',
      git_commit: 'success',
      fix_summary: 'primary',
    };
    return colors[opType] || 'default';
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const toggleExpand = (logId) => {
    setExpandedLog(expandedLog === logId ? null : logId);
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h3" gutterBottom>
        Operation Logs
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" gap={2}>
            <TextField
              label="Search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              sx={{ flexGrow: 1 }}
            />
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Filter by Type</InputLabel>
              <Select
                value={filter}
                label="Filter by Type"
                onChange={(e) => setFilter(e.target.value)}
              >
                <MenuItem value="all">All Operations</MenuItem>
                <MenuItem value="issue_detection">Issue Detection</MenuItem>
                <MenuItem value="llm_interaction">LLM Interaction</MenuItem>
                <MenuItem value="code_edit">Code Edit</MenuItem>
                <MenuItem value="git_commit">Git Commit</MenuItem>
                <MenuItem value="fix_summary">Fix Summary</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </CardContent>
      </Card>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell width={50}></TableCell>
              <TableCell>Timestamp</TableCell>
              <TableCell>Operation</TableCell>
              <TableCell>File</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {logs.map((log) => (
              <React.Fragment key={log.id}>
                <TableRow hover>
                  <TableCell>
                    <IconButton
                      size="small"
                      onClick={() => toggleExpand(log.id)}
                    >
                      <ExpandMoreIcon
                        sx={{
                          transform: expandedLog === log.id ? 'rotate(180deg)' : 'rotate(0deg)',
                          transition: '0.3s',
                        }}
                      />
                    </IconButton>
                  </TableCell>
                  <TableCell>{formatTimestamp(log.timestamp)}</TableCell>
                  <TableCell>
                    <Chip
                      label={log.operation_type}
                      color={getOperationColor(log.operation_type)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {log.file_path ? log.file_path.split('/').pop() : 'N/A'}
                  </TableCell>
                  <TableCell>
                    {log.details?.success !== undefined && (
                      <Chip
                        label={log.details.success ? 'Success' : 'Failed'}
                        color={log.details.success ? 'success' : 'error'}
                        size="small"
                      />
                    )}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell colSpan={5} sx={{ py: 0 }}>
                    <Collapse in={expandedLog === log.id} timeout="auto">
                      <Box sx={{ p: 2, bgcolor: 'grey.50' }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Details:
                        </Typography>
                        <pre style={{ overflow: 'auto', maxHeight: '300px' }}>
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      </Box>
                    </Collapse>
                  </TableCell>
                </TableRow>
              </React.Fragment>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {logs.length === 0 && (
        <Box textAlign="center" py={4}>
          <Typography color="text.secondary">
            No logs found
          </Typography>
        </Box>
      )}
    </Container>
  );
}

export default Logs;
