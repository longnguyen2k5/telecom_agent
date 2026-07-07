import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';

const RenameModal = ({ isOpen, onClose, initialTitle, onRename }) => {
  const [title, setTitle] = useState(initialTitle || '');

  useEffect(() => {
    if (isOpen) {
      setTitle(initialTitle || '');
    }
  }, [isOpen, initialTitle]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (title.trim()) {
      onRename(title.trim());
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 z-[60] flex items-center justify-center p-4">
      <div className="bg-card w-full max-w-sm rounded-xl border border-border shadow-2xl flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border/50">
          <h3 className="font-medium text-foreground">Rename chat</h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors">
            <X size={18} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-4 flex flex-col gap-4">
          <input
            type="text"
            autoFocus
            className="w-full bg-background border border-border rounded-lg px-3 py-2.5 text-[15px] outline-none text-foreground focus:border-primary transition-colors"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Enter new name..."
          />
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm font-medium border hover:bg-secondary text-foreground transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!title.trim() || title.trim() === initialTitle}
              className="px-4 py-2 rounded-lg text-sm font-medium bg-foreground text-background hover:opacity-90 disabled:opacity-50 transition-colors"
            >
              Save
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default RenameModal;
