import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  ListAlt as LogsIcon,
  CommitOutlined as CommitsIcon,
} from '@mui/icons-material';

import theme from './theme/theme';
import Dashboard from './pages/Dashboard';
import Logs from './pages/Logs';
import Commits from './pages/Commits';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          <AppBar position="static">
            <Toolbar>
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                Healr
              </Typography>
              <Button
                color="inherit"
                component={Link}
                to="/"
                startIcon={<DashboardIcon />}
              >
                Dashboard
              </Button>
              <Button
                color="inherit"
                component={Link}
                to="/logs"
                startIcon={<LogsIcon />}
              >
                Logs
              </Button>
              <Button
                color="inherit"
                component={Link}
                to="/commits"
                startIcon={<CommitsIcon />}
              >
                Commits
              </Button>
            </Toolbar>
          </AppBar>

          <Box component="main" sx={{ flexGrow: 1, bgcolor: 'background.default' }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/logs" element={<Logs />} />
              <Route path="/commits" element={<Commits />} />
            </Routes>
          </Box>

          <Box
            component="footer"
            sx={{
              py: 3,
              px: 2,
              mt: 'auto',
              bgcolor: 'background.paper',
            }}
          >
            <Container maxWidth="sm">
              <Typography variant="body2" color="text.secondary" align="center">
                Healr - AI-Powered Code Self-Healing System
              </Typography>
            </Container>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
