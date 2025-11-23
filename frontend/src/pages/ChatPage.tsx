import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Chip,
  CircularProgress,
  Drawer,
  List,
  ListItem,
  ListItemText,
  Divider,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  Send as SendIcon,
  Add as AddIcon,
  Security as SecurityIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: any[];
  security_info?: any;
  pii_redacted?: string[];
}

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<any[]>([]);
  const [securityAlert, setSecurityAlert] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/chat/history`);
      setConversations(response.data.conversations);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  };

  const loadConversation = async (convId: string) => {
    try {
      const response = await axios.get(`${API_URL}/api/chat/history/${convId}`);
      setConversationId(convId);
      
      // Convert backend message format to frontend Message format
      const loadedMessages: Message[] = response.data.messages.map((msg: any) => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp,
        sources: msg.sources,
        security_info: msg.security_info,
        pii_redacted: msg.pii_redacted,
      }));
      
      setMessages(loadedMessages);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const handleNewConversation = async () => {
    try {
      const response = await axios.post(`${API_URL}/api/chat/new`);
      setConversationId(response.data.conversation_id);
      setMessages([]);
    } catch (error) {
      console.error('Failed to create new conversation:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/api/chat/message`, {
        message: input,
        conversation_id: conversationId,
      });

      if (!conversationId) {
        setConversationId(response.data.conversation_id);
      }

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString(),
        sources: response.data.sources,
        security_info: response.data.security_info,
        pii_redacted: response.data.pii_redacted,
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Show security alerts
      if (response.data.security_info?.blocked) {
        setSecurityAlert(
          `Security threat detected: ${response.data.security_info.attack_type}`
        );
      }

      loadConversations();
    } catch (error: any) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, an error occurred. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Box sx={{ display: 'flex', height: '100%' }}>
      {/* Sidebar */}
      <Drawer
        variant="permanent"
        sx={{
          width: 280,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: 280,
            boxSizing: 'border-box',
            position: 'relative',
          },
        }}
      >
        <Box sx={{ p: 2 }}>
          <Box
            component="button"
            onClick={handleNewConversation}
            sx={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              p: 1.5,
              mb: 2,
              border: '1px solid',
              borderColor: 'primary.main',
              borderRadius: 1,
              bgcolor: 'transparent',
              color: 'primary.main',
              cursor: 'pointer',
              '&:hover': {
                bgcolor: 'primary.main',
                color: 'white',
              },
            }}
          >
            <AddIcon sx={{ mr: 1 }} />
            New Chat
          </Box>
        </Box>
        <Divider />
        <List sx={{ overflow: 'auto' }}>
          {conversations.map((conv) => (
            <ListItem
              key={conv.conversation_id}
              button
              selected={conv.conversation_id === conversationId}
              onClick={() => loadConversation(conv.conversation_id)}
            >
              <ListItemText
                primary={conv.preview || 'New Conversation'}
                secondary={new Date(conv.created_at).toLocaleDateString()}
              />
            </ListItem>
          ))}
        </List>
      </Drawer>

      {/* Main Chat Area */}
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', p: 2 }}>
        {/* Messages */}
        <Box sx={{ flexGrow: 1, overflow: 'auto', mb: 2 }}>
          {messages.length === 0 && (
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
              }}
            >
              <Typography variant="h5" color="text.secondary">
                Start a conversation
              </Typography>
            </Box>
          )}

          {messages.map((message, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                mb: 2,
              }}
            >
              <Paper
                elevation={1}
                sx={{
                  p: 2,
                  maxWidth: '70%',
                  bgcolor: message.role === 'user' ? 'primary.main' : 'grey.100',
                  color: message.role === 'user' ? 'white' : 'text.primary',
                }}
              >
                <ReactMarkdown>{message.content}</ReactMarkdown>

                {/* PII Redaction Badges */}
                {message.pii_redacted && message.pii_redacted.length > 0 && (
                  <Box sx={{ mt: 1, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                    {message.pii_redacted.map((type, idx) => (
                      <Chip
                        key={idx}
                        label={`${type} redacted`}
                        size="small"
                        color="warning"
                        icon={<SecurityIcon />}
                      />
                    ))}
                  </Box>
                )}

                <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.7 }}>
                  {new Date(message.timestamp).toLocaleTimeString()}
                </Typography>
              </Paper>
            </Box>
          ))}

          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
              <Paper elevation={1} sx={{ p: 2 }}>
                <CircularProgress size={20} />
                <Typography variant="body2" sx={{ ml: 2, display: 'inline' }}>
                  Thinking...
                </Typography>
              </Paper>
            </Box>
          )}

          <div ref={messagesEndRef} />
        </Box>

        {/* Input Area */}
        <Paper elevation={3} sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              disabled={loading}
            />
            <IconButton
              color="primary"
              onClick={handleSendMessage}
              disabled={loading || !input.trim()}
            >
              <SendIcon />
            </IconButton>
          </Box>
        </Paper>
      </Box>

      {/* Security Alert Snackbar */}
      <Snackbar
        open={!!securityAlert}
        autoHideDuration={6000}
        onClose={() => setSecurityAlert(null)}
      >
        <Alert severity="error" icon={<WarningIcon />}>
          {securityAlert}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ChatPage;
