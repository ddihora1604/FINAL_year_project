import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    List,
    ListItem,
    ListItemButton,
    ListItemText,
    Typography,
    Paper,
    Divider,
    CircularProgress,
} from '@mui/material';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const HistoryPage: React.FC = () => {
    const navigate = useNavigate();
    const [conversations, setConversations] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadConversations();
    }, []);

    const loadConversations = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/chat/history`);
            setConversations(response.data.conversations);
        } catch (error) {
            console.error('Failed to load conversations:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleConversationClick = (id: string) => {
        navigate(`/?id=${id}`);
    };

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
                Conversation History
            </Typography>
            <Paper elevation={2}>
                {loading ? (
                    <Box sx={{ p: 4, textAlign: 'center' }}>
                        <CircularProgress />
                    </Box>
                ) : (
                    <List>
                        {conversations.length === 0 ? (
                            <ListItem>
                                <ListItemText primary="No conversations found." />
                            </ListItem>
                        ) : (
                            conversations.map((conv, index) => (
                                <React.Fragment key={conv.conversation_id}>
                                    <ListItem disablePadding>
                                        <ListItemButton onClick={() => handleConversationClick(conv.conversation_id)}>
                                            <ListItemText
                                                primary={conv.preview || 'New Conversation'}
                                                secondary={new Date(conv.created_at).toLocaleString()}
                                            />
                                        </ListItemButton>
                                    </ListItem>
                                    {index < conversations.length - 1 && <Divider />}
                                </React.Fragment>
                            ))
                        )}
                    </List>
                )}
            </Paper>
        </Box>
    );
};

export default HistoryPage;
