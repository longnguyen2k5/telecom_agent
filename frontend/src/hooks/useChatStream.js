import { useState, useCallback } from 'react';
import { chatRequest } from '../api';

const useChatStream = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Đây là bản mô phỏng đơn giản. Thực tế có thể dùng SSE hoặc Websocket
  const sendMessage = useCallback(async (content, sessionId) => {
    if (!content.trim()) return;

    const userMessage = { id: Date.now(), role: 'user', content };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Giả sử API trả về response JSON thông thường (không stream)
      // Để làm stream thật (SSE), cần dùng fetch API và đọc stream reader
      const response = await chatRequest({ session_id: sessionId, message: content });
      
      const agentMessage = {
        id: Date.now() + 1,
        role: 'agent',
        content: response.data.reply,
        toolCalls: response.data.toolCalls || []
      };
      
      setMessages((prev) => [...prev, agentMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      // Optionally handle error state
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { messages, setMessages, sendMessage, isLoading };
};

export default useChatStream;
