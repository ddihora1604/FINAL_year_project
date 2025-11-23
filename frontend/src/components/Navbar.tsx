import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Tooltip,
} from '@mui/material';
import {
  Chat as ChatIcon,
  Dashboard as DashboardIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <AppBar position="static" elevation={1}>
      <Toolbar>
        <SecurityIcon sx={{ mr: 2 }} />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Secure RAG Chatbot
        </Typography>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Chat Interface">
            <Button
              color="inherit"
              startIcon={<ChatIcon />}
              onClick={() => navigate('/')}
              variant={location.pathname === '/' ? 'outlined' : 'text'}
            >
              Chat
            </Button>
          </Tooltip>

          <Tooltip title="Monitoring Dashboard">
            <Button
              color="inherit"
              startIcon={<DashboardIcon />}
              onClick={() => navigate('/dashboard')}
              variant={location.pathname === '/dashboard' ? 'outlined' : 'text'}
            >
              Dashboard
            </Button>
          </Tooltip>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;
