import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Avatar,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Security as SecurityIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const GRAFANA_URL = process.env.REACT_APP_GRAFANA_URL || 'http://localhost:3001';

interface MetricsSummary {
  total_queries: number;
  blocked_attacks: number;
  avg_response_time: number;
  success_rate: number;
  pii_redacted_count: number;
}

const DashboardPage: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsSummary>({
    total_queries: 0,
    blocked_attacks: 0,
    avg_response_time: 0,
    success_rate: 0,
    pii_redacted_count: 0,
  });

  useEffect(() => {
    loadMetrics();
    const interval = setInterval(loadMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadMetrics = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/metrics/summary`);
      setMetrics(response.data);
    } catch (error) {
      console.error('Failed to load metrics:', error);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Metrics Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)', border: '1px solid rgba(255,255,255,0.1)' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                  <TrendingUpIcon />
                </Avatar>
                <Typography variant="h6" color="text.secondary">Total Queries</Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 'bold' }}>{metrics.total_queries}</Typography>
              <Typography variant="caption" color="text.secondary">
                Last 24 hours
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)', border: '1px solid rgba(255,255,255,0.1)' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'error.main', mr: 2 }}>
                  <SecurityIcon />
                </Avatar>
                <Typography variant="h6" color="text.secondary">Attacks Blocked</Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 'bold', color: 'error.main' }}>{metrics.blocked_attacks}</Typography>
              <Typography variant="caption" color="text.secondary">
                Security events
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)', border: '1px solid rgba(255,255,255,0.1)' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                  <SpeedIcon />
                </Avatar>
                <Typography variant="h6" color="text.secondary">Avg Response</Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                {metrics.avg_response_time.toFixed(2)}s
              </Typography>
              <Typography variant="caption" color="text.secondary">
                P95 Latency
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)', border: '1px solid rgba(255,255,255,0.1)' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                  <CheckCircleIcon />
                </Avatar>
                <Typography variant="h6" color="text.secondary">Success Rate</Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 'bold' }}>{metrics.success_rate.toFixed(1)}%</Typography>
              <Typography variant="caption" color="text.secondary">
                Query success
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Grafana Dashboard */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          Grafana Dashboards
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Click below to access the full Grafana monitoring dashboards
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <a
            href={GRAFANA_URL}
            target="_blank"
            rel="noopener noreferrer"
            style={{ textDecoration: 'none' }}
          >
            <Card sx={{ minWidth: 200, cursor: 'pointer', '&:hover': { boxShadow: 6 } }}>
              <CardContent>
                <Typography variant="h6" color="primary">
                  Open Grafana
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  View detailed metrics and dashboards
                </Typography>
              </CardContent>
            </Card>
          </a>
        </Box>

        <Box sx={{ mt: 3 }}>
          <Typography variant="body2" color="text.secondary">
            📊 Access Grafana at: <a href={GRAFANA_URL} target="_blank" rel="noopener noreferrer">{GRAFANA_URL}</a>
            <br />
            🔑 Default credentials: admin / admin
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
};

export default DashboardPage;
