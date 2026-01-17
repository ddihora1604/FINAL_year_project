import React, { useState, useEffect } from 'react';
import {
    Box,
    Typography,
    Paper,
    TextField,
    Button,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Grid,
    Snackbar,
    Alert,
} from '@mui/material';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const SettingsPage: React.FC = () => {
    const [config, setConfig] = useState<any>({
        model_name: 'gpt-3.5-turbo',
        temperature: 0.7,
        max_tokens: 2048,
    });
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);

    useEffect(() => {
        loadConfig();
    }, []);

    const loadConfig = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/system/config`);
            if (response.data) {
                setConfig(response.data);
            }
        } catch (error) {
            console.error('Failed to load config:', error);
            // Fallback or error handling
        }
    };

    const handleSave = async () => {
        try {
            setLoading(true);
            await axios.post(`${API_URL}/api/system/config`, config);
            setSuccess(true);
        } catch (error) {
            console.error('Failed to save config:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
                System Settings
            </Typography>
            <Paper elevation={2} sx={{ p: 3 }}>
                <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                        <FormControl fullWidth>
                            <InputLabel>Model</InputLabel>
                            <Select
                                value={config.model_name}
                                label="Model"
                                onChange={(e) => setConfig({ ...config, model_name: e.target.value })}
                            >
                                <MenuItem value="gpt-3.5-turbo">GPT-3.5 Turbo</MenuItem>
                                <MenuItem value="gpt-4">GPT-4</MenuItem>
                                <MenuItem value="llama-2-70b">Llama 2 70B</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <TextField
                            fullWidth
                            label="Temperature"
                            type="number"
                            inputProps={{ step: 0.1, min: 0, max: 1 }}
                            value={config.temperature}
                            onChange={(e) =>
                                setConfig({ ...config, temperature: parseFloat(e.target.value) })
                            }
                        />
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <TextField
                            fullWidth
                            label="Max Tokens"
                            type="number"
                            value={config.max_tokens}
                            onChange={(e) =>
                                setConfig({ ...config, max_tokens: parseInt(e.target.value) })
                            }
                        />
                    </Grid>
                    <Grid item xs={12}>
                        <Button
                            variant="contained"
                            color="primary"
                            onClick={handleSave}
                            disabled={loading}
                        >
                            Save Changes
                        </Button>
                    </Grid>
                </Grid>
            </Paper>
            <Snackbar
                open={success}
                autoHideDuration={6000}
                onClose={() => setSuccess(false)}
            >
                <Alert severity="success" sx={{ width: '100%' }}>
                    Settings saved successfully!
                </Alert>
            </Snackbar>
        </Box>
    );
};

export default SettingsPage;
