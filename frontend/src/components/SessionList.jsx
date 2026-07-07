import React, { useState } from 'react';
import { Plus, MessageSquare, MoreVertical, Edit, Trash } from 'lucide-react';

const SessionList = ({ sessions, currentSessionId, onSelectSession, onNewSession, onOpenChats, onRenameSessionInit, onDeleteSessionInit }) => {
  const [menuOpenId, setMenuOpenId] = useState(null);
  // Get top 15 recent sessions for the sidebar
  const recentSessions = sessions.slice(0, 15);

  return (
    <div className="w-[260px] bg-background border-r flex flex-col flex-shrink-0">
      <div className="p-4 pl-5">
        <h1 className="font-serif text-xl font-medium text-foreground mb-6">Telecom Agent</h1>
        
        <div className="space-y-1 mb-8">
          <button 
            onClick={onNewSession}
            className="w-full flex items-center gap-3 px-2 py-2 text-[15px] font-medium text-foreground hover:bg-secondary rounded-lg transition-colors group"
          >
            <div className="w-5 h-5 flex items-center justify-center rounded bg-secondary group-hover:bg-background border border-border">
              <Plus size={14} />
            </div>
            New chat
          </button>
          
          <button 
            onClick={onOpenChats}
            className="w-full flex items-center gap-3 px-2 py-2 text-[15px] font-medium text-foreground hover:bg-secondary rounded-lg transition-colors"
          >
            <MessageSquare size={18} className="text-muted-foreground" />
            Chats
          </button>
        </div>
        
        <div className="text-xs font-medium text-muted-foreground mb-2 px-2 uppercase tracking-wider">
          Recents
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto px-3 space-y-0.5 pb-4 custom-scrollbar">
        {recentSessions?.map((session) => (
          <div 
            key={session.id}
            onClick={(e) => {
              if (!e.target.closest('.action-menu')) {
                onSelectSession(session.id);
              }
            }}
            className={`group flex items-center justify-between px-2 py-2 mx-1 rounded-lg cursor-pointer transition-colors ${
              currentSessionId === session.id 
                ? 'bg-secondary text-foreground' 
                : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
            }`}
          >
            <div className="text-[14px] truncate flex-1 pr-2 font-medium">
              {session.title || 'New Chat'}
            </div>
            
            <div className="relative action-menu flex-shrink-0">
              <button 
                className={`p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-background transition-colors ${menuOpenId === session.id ? 'opacity-100 bg-background text-foreground' : 'opacity-0 group-hover:opacity-100'}`}
                onClick={(e) => {
                  e.stopPropagation();
                  setMenuOpenId(menuOpenId === session.id ? null : session.id);
                }}
              >
                <MoreVertical size={14} />
              </button>
              
              {menuOpenId === session.id && (
                <div className="absolute right-0 top-full mt-1 w-36 bg-popover border shadow-lg rounded-lg py-1 z-50 animate-in fade-in zoom-in duration-100">
                  <button 
                    className="w-full text-left px-3 py-2 text-sm flex items-center gap-2 hover:bg-secondary text-foreground"
                    onClick={(e) => {
                      e.stopPropagation();
                      setMenuOpenId(null);
                      onRenameSessionInit(session.id, session.title);
                    }}
                  >
                    <Edit size={14} /> Rename
                  </button>
                  <button 
                    className="w-full text-left px-3 py-2 text-sm flex items-center gap-2 hover:bg-red-500/10 text-red-500"
                    onClick={(e) => {
                      e.stopPropagation();
                      setMenuOpenId(null);
                      onDeleteSessionInit(session.id);
                    }}
                  >
                    <Trash size={14} /> Delete
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
        
        {menuOpenId && (
          <div 
            className="fixed inset-0 z-40" 
            onClick={(e) => {
              e.stopPropagation();
              setMenuOpenId(null);
            }} 
          />
        )}
      </div>
    </div>
  );
};

export default SessionList;
