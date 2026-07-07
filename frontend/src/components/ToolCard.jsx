import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Terminal, FileText } from 'lucide-react';

const ToolCard = ({ tool }) => {
  const [expanded, setExpanded] = useState(false);

  const getIcon = () => {
    if (tool.type === 'run_command') return <Terminal size={16} />;
    return <FileText size={16} />;
  };

  return (
    <div className="bg-card border rounded-lg p-3 my-3 text-sm text-muted-foreground flex flex-col gap-2 max-w-xl">
      <div 
        className="flex items-center gap-2 font-medium text-foreground cursor-pointer select-none"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        {getIcon()}
        <span>{tool.name || tool.description || 'Tool Call'}</span>
        {tool.status === 'running' && <span className="ml-2 text-xs italic text-blue-400">running...</span>}
        {tool.status === 'error' && <span className="ml-2 text-xs italic text-red-400">error</span>}
      </div>
      
      {expanded && (
        <div className="bg-black/50 rounded p-2 font-mono overflow-x-auto text-xs border border-border/50">
          {tool.args && (
            <div className="mb-2">
              <span className="text-primary/70">Arguments:</span>
              <pre className="mt-1">{JSON.stringify(tool.args, null, 2)}</pre>
            </div>
          )}
          {tool.result && (
            <div>
              <span className="text-primary/70">Result:</span>
              <pre className="mt-1">{JSON.stringify(tool.result, null, 2)}</pre>
            </div>
          )}
          {tool.details && <code>{tool.details}</code>}
        </div>
      )}
    </div>
  );
};

export default ToolCard;
