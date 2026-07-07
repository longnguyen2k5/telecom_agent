import React, { useState } from 'react';
import { X, Search, MoreVertical, Trash, Edit } from 'lucide-react';

const ChatsModal = ({ isOpen, onClose, sessions, onSelectSession, onRenameSessionInit, onDeleteSessionInit }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [menuOpenId, setMenuOpenId] = useState(null);

  if (!isOpen) return null;

  const filteredSessions = sessions.filter(s => 
    (s.title || 'New Chat').toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-card w-full max-w-4xl h-[85vh] rounded-2xl flex flex-col border border-border shadow-2xl relative overflow-hidden">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border/50">
          <h2 className="text-xl font-serif text-foreground">Chats</h2>
          <button 
            onClick={onClose}
            className="p-2 text-muted-foreground hover:text-foreground rounded-md hover:bg-secondary transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Search Bar */}
        <div className="px-6 py-4 bg-background">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
            <input 
              type="text" 
              placeholder="Search chats..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-secondary border-none rounded-lg pl-10 pr-4 py-2.5 text-[15px] outline-none text-foreground placeholder:text-muted-foreground"
            />
          </div>
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto px-2 pb-4">
          <div className="flex flex-col">
            {filteredSessions.map(session => (
              <div 
                key={session.id} 
                className="group flex items-center justify-between px-4 py-3 mx-2 rounded-xl hover:bg-secondary cursor-pointer transition-colors"
                onClick={(e) => {
                  // Don't navigate if clicking on menu
                  if (!e.target.closest('.action-menu')) {
                    onSelectSession(session.id);
                    onClose();
                  }
                }}
              >
                <div className="text-[15px] text-foreground font-medium truncate pr-4">
                  {session.title || 'New Chat'}
                </div>
                
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {new Date(session.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </span>
                  
                  <div className="relative action-menu">
                    <button 
                      className={`p-1.5 rounded-md hover:bg-background text-muted-foreground hover:text-foreground transition-colors ${menuOpenId === session.id ? 'opacity-100 bg-background text-foreground' : 'opacity-0 group-hover:opacity-100'}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        setMenuOpenId(menuOpenId === session.id ? null : session.id);
                      }}
                    >
                      <MoreVertical size={16} />
                    </button>
                    
                    {menuOpenId === session.id && (
                      <div className="absolute right-0 top-full mt-1 w-36 bg-popover border shadow-lg rounded-lg py-1 z-10 animate-in fade-in zoom-in duration-100">
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
              </div>
            ))}
            
            {filteredSessions.length === 0 && (
              <div className="text-center py-10 text-muted-foreground text-sm">
                No chats found
              </div>
            )}
          </div>
        </div>
        
        {/* Click outside to close menu overlay */}
        {menuOpenId && (
          <div 
            className="fixed inset-0 z-0" 
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

export default ChatsModal;
