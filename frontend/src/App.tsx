import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';
import ChatPage from './pages/ChatPage';
import DashboardPage from './pages/DashboardPage';
import Navbar from './components/Navbar';

function App() {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Navbar />
      <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
        </Routes>
      </Box>
    </Box>
  );
}

export default App;
