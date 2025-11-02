import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  Box,
  Typography,
  CircularProgress,
} from '@mui/material';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import theme from './theme/theme';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Devices from './pages/Devices';
import Deployments from './pages/Deployments';
import DeploymentDetail from './pages/DeploymentDetail';
import Rings from './pages/Rings';
import Simulator from './pages/Simulator';

function App() {
  const [serverDown, setServerDown] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const checkServer = async () => {
      try {
        const response = await fetch('http://localhost:8000/', {
          method: 'GET',
          signal: AbortSignal.timeout(3000), // 3 second timeout
        });
        
        if (response.ok) {
          setServerDown(false);
          setChecking(false);
        } else {
          setServerDown(true);
          setChecking(false);
        }
      } catch (error) {
        setServerDown(true);
        setChecking(false);
      }
    };

    // Initial check
    checkServer();

    // Check every 5 seconds if server is down
    const interval = setInterval(() => {
      if (serverDown || checking) {
        checkServer();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [serverDown, checking]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      
      {/* Non-closable server down dialog */}
      <Dialog
        open={serverDown}
        aria-labelledby="server-down-dialog"
        disableEscapeKeyDown
        PaperProps={{
          sx: {
            minWidth: 400,
            backgroundColor: '#fff3e0',
            border: '2px solid #ff9800',
          },
        }}
      >
        <DialogTitle
          id="server-down-dialog"
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 2,
            color: '#e65100',
          }}
        >
          <ErrorOutlineIcon sx={{ fontSize: 40 }} />
          <Typography variant="h6" component="div">
            FlexDeploy Server Not Running
          </Typography>
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ color: '#bf360c', mb: 2 }}>
            The FlexDeploy backend server is not accessible. Please start the server to use the application.
          </DialogContentText>
          
          <Box sx={{ bgcolor: '#fff', p: 2, borderRadius: 1, border: '1px solid #ffb74d' }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1, color: '#e65100' }}>
              To start the server:
            </Typography>
            <Typography
              variant="body2"
              component="pre"
              sx={{
                fontFamily: 'monospace',
                bgcolor: '#263238',
                color: '#aed581',
                p: 1.5,
                borderRadius: 1,
                overflow: 'auto',
              }}
            >
              cd /path/to/flexDeploy{'\n'}python -m server.main
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2, color: '#f57c00' }}>
            <CircularProgress size={20} sx={{ color: '#ff9800' }} />
            <Typography variant="body2">
              Checking server status...
            </Typography>
          </Box>
        </DialogContent>
      </Dialog>

      <Router>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="devices" element={<Devices />} />
            <Route path="deployments" element={<Deployments />} />
            <Route path="deployments/:id" element={<DeploymentDetail />} />
            <Route path="rings" element={<Rings />} />
          </Route>
          {/* Standalone simulator page without layout */}
          <Route path="/simulator" element={<Simulator />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
