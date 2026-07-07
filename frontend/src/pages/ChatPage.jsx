import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Send, Pen } from 'lucide-react';
import ChatBubble from '../components/ChatBubble';
import SessionList from '../components/SessionList';
import ChatsModal from '../components/ChatsModal';
import RenameModal from '../components/RenameModal';
import ConfirmModal from '../components/ConfirmModal';
import { getSessions, createSession, getSessionMessages, renameSession, deleteSession, CHAT_API_URL } from '../api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const ChatPage = () => {
  const queryClient = useQueryClient();
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [inputValue, setInputValue] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const [isChatsModalOpen, setIsChatsModalOpen] = useState(false);
  const [renameModalData, setRenameModalData] = useState({ isOpen: false, id: null, title: '' });
  const [confirmModalData, setConfirmModalData] = useState({ isOpen: false, id: null });
  const [blockedError, setBlockedError] = useState(null);
  const [isBlocked, setIsBlocked] = useState(false);
  const messagesEndRef = useRef(null);
  const username = localStorage.getItem('username') || 'User';

  const samplePrompts = [
    "Kiểm tra cho tôi xem có sự kiện HIGH_LOAD nào gần đây không",
    "Kiểm tra cho tôi policy ngày hôm nay cập nhật lên mới nhất theo trạng thái hiện tại",
    "Tóm tắt trạng thái các node mạng trong 24h qua"
  ];

  // Queries
  const { data: sessions = [] } = useQuery({
    queryKey: ['sessions'],
    queryFn: async () => {
      const res = await getSessions();
      return res.data;
    }
  });

  const { data: history = [] } = useQuery({
    queryKey: ['messages', currentSessionId],
    queryFn: async () => {
      if (!currentSessionId) return [];
      const res = await getSessionMessages(currentSessionId);
      return res.data.map(msg => ({
        ...msg,
        toolCalls: msg.tool_calls || msg.toolCalls || []
      }));
    },
    enabled: !!currentSessionId
  });

  // Local state for optimistic UI mapping
  const [localMessages, setLocalMessages] = useState([]);

  const prevSessionIdRef = useRef(null);

  useEffect(() => {
    if (prevSessionIdRef.current !== currentSessionId) {
      if (!(isStreaming && prevSessionIdRef.current === null)) {
        setLocalMessages(history);
      }
      prevSessionIdRef.current = currentSessionId;
    } else if (history.length > 0 && !isStreaming && !isBlocked) {
      setLocalMessages(history);
    }
  }, [history, currentSessionId, isStreaming, isBlocked]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [localMessages, isStreaming]);

  // Mutations
  const renameSessionMutation = useMutation({
    mutationFn: ({ id, title }) => renameSession(id, title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    }
  });

  const deleteSessionMutation = useMutation({
    mutationFn: (id) => deleteSession(id),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      if (currentSessionId === deletedId) {
        setCurrentSessionId(null);
        setLocalMessages([]);
      }
    }
  });

  const resetTextareas = () => {
    const textareas = document.querySelectorAll('.chat-textarea');
    textareas.forEach(ta => ta.style.height = 'auto');
  };

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${e.target.scrollHeight}px`;
  };

  const handleSend = async () => {
    if (!inputValue.trim() || isStreaming) return;
    
    setBlockedError(null);
    setIsBlocked(false);
    const content = inputValue;
    setInputValue('');
    resetTextareas();
    
    let targetSessionId = currentSessionId;
    let isNewSession = false;
    if (!targetSessionId) {
      try {
        setIsCreatingSession(true);
        const title = content.length > 30 ? content.substring(0, 30) + '...' : content;
        const res = await createSession(title);
        targetSessionId = res.data.id;
        setCurrentSessionId(targetSessionId);
        isNewSession = true;
        queryClient.invalidateQueries({ queryKey: ['sessions'] });
      } catch (err) {
        console.error('Failed to create session automatically', err);
        setIsCreatingSession(false);
        return;
      } finally {
        setIsCreatingSession(false);
      }
    }
    
    const userMessage = { id: Date.now(), role: 'user', content };
    setLocalMessages(prev => [...prev, userMessage]);
    
    setIsStreaming(true);
    const agentMessageId = Date.now() + 1;
    setLocalMessages(prev => [...prev, { id: agentMessageId, role: 'agent', content: '', toolCalls: [] }]);
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(CHAT_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ session_id: targetSessionId, message: content })
      });
      
      if (!response.ok) throw new Error('Network response was not ok');
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = '';
      let accumulatedThought = '';
      let buffer = '';
      let wasBlocked = false;
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const eventChunks = buffer.split('\n\n');
        buffer = eventChunks.pop();
        
        for (const eventChunk of eventChunks) {
          const lines = eventChunk.split('\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const dataStr = line.substring(6).trim();
                if (!dataStr) continue;
                const data = JSON.parse(dataStr);
                
                if (data.type === 'text') {
                  accumulatedContent += data.content;
                  setLocalMessages(prev => prev.map(msg => 
                    msg.id === agentMessageId ? { ...msg, content: accumulatedContent } : msg
                  ));
                } else if (data.type === 'thought') {
                  accumulatedThought += data.content;
                  setLocalMessages(prev => prev.map(msg => 
                    msg.id === agentMessageId ? { ...msg, thought: accumulatedThought } : msg
                  ));
                } else if (data.type === 'tool_start') {
                  setLocalMessages(prev => prev.map(msg => {
                    if (msg.id === agentMessageId) {
                      return {
                        ...msg,
                        toolCalls: [...(msg.toolCalls || []), { name: data.name, args: data.args, status: 'running' }]
                      };
                    }
                    return msg;
                  }));
                } else if (data.type === 'tool_result') {
                  setLocalMessages(prev => prev.map(msg => {
                    if (msg.id === agentMessageId) {
                      const updatedTools = [...(msg.toolCalls || [])];
                      const idx = updatedTools.findIndex(t => t.name === data.name && t.status === 'running');
                      if (idx !== -1) {
                         updatedTools[idx] = { ...updatedTools[idx], result: data.result, status: 'success' };
                      }
                      return { ...msg, toolCalls: updatedTools };
                    }
                    return msg;
                  }));
                } else if (data.type === 'done') {
                  setLocalMessages(prev => prev.map(msg => 
                    msg.id === agentMessageId ? { 
                      ...msg, 
                      content: data.full_text || '', 
                      thought: data.thought || '',
                      toolCalls: data.tools_used || [] 
                    } : msg
                  ));
                  if (data.full_text.includes('Yêu cầu bị chặn')) {
                    wasBlocked = true;
                    setIsBlocked(true);
                    if (isNewSession) {
                      deleteSession(targetSessionId).then(() => {
                        setCurrentSessionId(null);
                        setLocalMessages([]);
                        setBlockedError(data.full_text);
                        queryClient.invalidateQueries({ queryKey: ['sessions'] });
                      }).catch(console.error);
                    }
                  }
                }
              } catch (e) {
                console.error('Error parsing SSE data', e, line);
              }
            }
          }
        }
      }
      if (!wasBlocked) {
        queryClient.invalidateQueries({ queryKey: ['messages', targetSessionId] });
      }
    } catch (error) {
      console.error('Chat error:', error);
      setLocalMessages(prev => prev.map(msg => 
        msg.id === agentMessageId ? { ...msg, content: 'Sorry, there was an error processing your request.' } : msg
      ));
    } finally {
      setIsStreaming(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      <SessionList 
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={setCurrentSessionId}
        onNewSession={() => {
          setCurrentSessionId(null);
          setLocalMessages([]);
        }}
        onOpenChats={() => setIsChatsModalOpen(true)}
        onRenameSessionInit={(id, title) => setRenameModalData({ isOpen: true, id, title })}
        onDeleteSessionInit={(id) => setConfirmModalData({ isOpen: true, id })}
      />

      <ChatsModal 
        isOpen={isChatsModalOpen}
        onClose={() => setIsChatsModalOpen(false)}
        sessions={sessions}
        onSelectSession={setCurrentSessionId}
        onRenameSessionInit={(id, title) => setRenameModalData({ isOpen: true, id, title })}
        onDeleteSessionInit={(id) => setConfirmModalData({ isOpen: true, id })}
      />

      <ConfirmModal
        isOpen={confirmModalData.isOpen}
        onClose={() => setConfirmModalData({ isOpen: false, id: null })}
        title="Delete Session"
        message="Are you sure you want to delete this chat session? This action cannot be undone."
        onConfirm={() => {
          if (confirmModalData.id) deleteSessionMutation.mutate(confirmModalData.id);
        }}
      />

      <RenameModal
        isOpen={renameModalData.isOpen}
        onClose={() => setRenameModalData({ isOpen: false, id: null, title: '' })}
        initialTitle={renameModalData.title}
        onRename={(newTitle) => renameSessionMutation.mutate({ id: renameModalData.id, title: newTitle })}
      />
      
      <div className="flex-1 flex flex-col relative h-full">
        {currentSessionId ? (
          <>
            <div className="h-14 px-4 flex justify-between items-center border-b font-medium text-foreground shrink-0 group">
              <div className="flex items-center gap-2">
                {sessions.find(s => s.id === currentSessionId)?.title || 'Chat Session'}
                <button 
                  className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-foreground p-1 rounded-md"
                  onClick={() => {
                    const sessionTitle = sessions.find(s => s.id === currentSessionId)?.title || '';
                    setRenameModalData({ isOpen: true, id: currentSessionId, title: sessionTitle });
                  }}
                  title="Rename session"
                >
                  <Pen size={14} />
                </button>
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto py-6">
              {localMessages.length > 0 ? (
                <div className="max-w-3xl mx-auto px-6 flex flex-col">
                  {localMessages.map((msg) => (
                    <ChatBubble key={msg.id} message={msg} />
                  ))}
                  {isStreaming && localMessages[localMessages.length - 1]?.content === '' && (
                    <div className="mb-6 flex flex-col items-start opacity-50">
                      <div className="font-semibold mb-1 text-sm text-primary flex items-center gap-2">
                        <span className="text-xl">✻</span> Agent is typing...
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              ) : (
                <div className="h-full flex flex-col justify-center items-center text-center p-6">
                  <h1 className="text-[2.5rem] font-serif text-primary mb-8">✻ Back at it, {username}</h1>
                  <div className="w-full max-w-2xl p-0">
                    <div className="bg-card border rounded-2xl p-3 px-4 flex items-end gap-3 shadow-sm focus-within:border-muted-foreground transition-colors">
                      <textarea 
                        className="chat-textarea flex-1 bg-transparent border-none text-foreground font-sans text-[15px] resize-none max-h-48 min-h-6 overflow-y-auto custom-scrollbar outline-none p-0 leading-relaxed placeholder:text-muted-foreground"
                        placeholder="Write a message..."
                        value={inputValue}
                        onChange={handleInputChange}
                        onKeyDown={handleKeyDown}
                        rows={1}
                      />
                      <button 
                        className="bg-foreground text-background border-none rounded-full w-8 h-8 flex justify-center items-center cursor-pointer transition-transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
                        onClick={handleSend}
                        disabled={!inputValue.trim() || isStreaming}
                      >
                        {isStreaming ? <div className="w-4 h-4 border-2 border-background border-t-transparent rounded-full animate-spin" /> : <Send size={15} />}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col justify-center items-center text-center p-6">
            <h1 className="text-[2.5rem] font-serif text-primary mb-8">✻ Back at it, {username}</h1>
            
            {blockedError && (
              <div className="mb-6 w-full max-w-2xl bg-destructive/80 border border-destructive text-white px-6 py-4 rounded-xl text-left text-[15px] shadow-sm animate-in fade-in slide-in-from-bottom-2">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {blockedError}
                </ReactMarkdown>
              </div>
            )}
            
            <div className="w-full max-w-2xl p-0">
              <div className="bg-card border rounded-2xl p-3 px-4 flex items-end gap-3 shadow-sm focus-within:border-muted-foreground transition-colors">
                <textarea 
                  className="chat-textarea flex-1 bg-transparent border-none text-foreground font-sans text-[15px] resize-none max-h-48 min-h-6 overflow-y-auto custom-scrollbar outline-none p-0 leading-relaxed placeholder:text-muted-foreground"
                  placeholder="How can I help you today?"
                  value={inputValue}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  rows={1}
                />
                <button 
                  className="bg-foreground text-background border-none rounded-full w-8 h-8 flex justify-center items-center cursor-pointer transition-transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
                  onClick={handleSend}
                  disabled={!inputValue.trim() || isCreatingSession}
                >
                  {isCreatingSession ? <div className="w-4 h-4 border-2 border-background border-t-transparent rounded-full animate-spin" /> : <Send size={15} />}
                </button>
              </div>
            </div>
            
            <div className="flex flex-col gap-2 mt-4 w-full max-w-2xl px-2">
              {samplePrompts.map((prompt, index) => (
                <button 
                  key={index}
                  onClick={() => {
                    setInputValue(prompt);
                    const textareas = document.querySelectorAll('.chat-textarea');
                    textareas.forEach(ta => {
                      ta.value = prompt;
                      ta.style.height = 'auto';
                      ta.style.height = `${ta.scrollHeight}px`;
                    });
                  }}
                  className="bg-card border border-border/60 text-muted-foreground px-4 py-3 rounded-xl text-[14px] text-left transition-all hover:bg-secondary hover:text-foreground w-full shadow-sm hover:shadow-md animate-slide-down opacity-0"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Fixed Input Box */}
        {currentSessionId && localMessages.length > 0 && (
          <div className="p-6 w-full max-w-3xl mx-auto shrink-0 pb-8">
            <div className="bg-card border rounded-2xl p-3 px-4 flex items-end gap-3 shadow-sm focus-within:border-muted-foreground transition-colors">
              <textarea 
                className="chat-textarea flex-1 bg-transparent border-none text-foreground font-sans text-[15px] resize-none max-h-48 min-h-6 overflow-y-auto custom-scrollbar outline-none p-0 leading-relaxed placeholder:text-muted-foreground"
                placeholder="Write a message..."
                value={inputValue}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                rows={1}
              />
              <button 
                className="bg-foreground text-background border-none rounded-full w-8 h-8 flex justify-center items-center cursor-pointer transition-transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
                onClick={handleSend}
                disabled={!inputValue.trim() || isStreaming}
              >
                <Send size={15} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatPage;
