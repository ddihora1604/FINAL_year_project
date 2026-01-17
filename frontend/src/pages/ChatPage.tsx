import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Chip,
  CircularProgress,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  Send as SendIcon,
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
  const [searchParams, setSearchParams] = useSearchParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [securityAlert, setSecurityAlert] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const idParam = searchParams.get('id');

  useEffect(() => {
    if (idParam && idParam !== conversationId) {
      setConversationId(idParam);
      loadConversation(idParam);
    } else if (!idParam && conversationId) {
      // Reset if URL param is removed
      setConversationId(null);
      setMessages([]);
    }
  }, [idParam, conversationId]);

  const loadConversation = async (convId: string) => {
    try {
      setLoading(true);
      setMessages([]);
      const response = await axios.get(`${API_URL}/api/chat/history/${convId}`);

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
    } finally {
      setLoading(false);
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
        setSearchParams({ id: response.data.conversation_id });
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
    <Box sx={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 100px)' }}>
      {/* Messages */}
      <Box sx={{ flexGrow: 1, overflow: 'auto', mb: 2, p: 2 }}>
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
              mb: 3,
            }}
          >
            <Paper
              elevation={message.role === 'user' ? 4 : 1}
              sx={{
                p: 2,
                maxWidth: '70%',
                borderRadius: 2,
                borderTopRightRadius: message.role === 'user' ? 0 : 2,
                borderTopLeftRadius: message.role === 'assistant' ? 0 : 2,
                background: message.role === 'user'
                  ? 'linear-gradient(135deg, #7b1fa2 0%, #4a0072 100%)'
                  : 'rgba(255, 255, 255, 0.05)',
                color: message.role === 'user' ? '#ffffff' : 'text.primary',
                border: message.role === 'assistant' ? '1px solid rgba(255, 255, 255, 0.1)' : 'none',
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
                      variant="outlined"
                      icon={<SecurityIcon />}
                      sx={{ borderColor: 'warning.main', color: 'warning.main' }}
                    />
                  ))}
                </Box>
              )}

              <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.6, textAlign: 'right' }}>
                {new Date(message.timestamp).toLocaleTimeString()}
              </Typography>
            </Paper>
          </Box>
        ))}

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 2 }}>
            <Paper elevation={0} sx={{ p: 2, bgcolor: 'transparent', display: 'flex', alignItems: 'center' }}>
              <CircularProgress size={20} sx={{ mr: 2 }} />
              <Typography variant="body2" color="text.secondary">
                Analyzing data...
              </Typography>
            </Paper>
          </Box>
        )}

        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Paper
        elevation={6}
        sx={{
          p: '2px 4px',
          display: 'flex',
          alignItems: 'center',
          borderRadius: 4,
          bgcolor: 'background.paper',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          mb: 2
        }}
      >
        <TextField
          sx={{ ml: 1, flex: 1 }}
          placeholder="Ask anything about your data..."
          variant="standard"
          multiline
          maxRows={4}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={loading}
          InputProps={{
            disableUnderline: true,
          }}
        />
        <IconButton
          color="primary"
          sx={{ p: '10px' }}
          onClick={handleSendMessage}
          disabled={loading || !input.trim()}
        >
          <SendIcon />
        </IconButton>
      </Paper>

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
