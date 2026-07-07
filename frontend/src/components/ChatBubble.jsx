import React from 'react';
import ToolCard from './ToolCard';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const ChatBubble = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`mb-6 flex flex-col leading-relaxed ${isUser ? 'items-end' : 'items-start'}`}>
      {!isUser && (
        <div className="font-semibold mb-1 text-sm text-primary flex items-center gap-2">
          <span className="text-xl">✻</span> Telecom Agent
        </div>
      )}
      
      {!isUser && message.toolCalls?.map((tool, idx) => (
        <ToolCard key={idx} tool={tool} />
      ))}
      
      <div className={`px-4 py-3 rounded-xl max-w-[85%] text-[15px] ${
        isUser 
          ? 'bg-secondary rounded-br-sm text-foreground' 
          : 'bg-transparent pl-0 max-w-full text-foreground'
      }`}>
        {isUser ? (
          <div className="whitespace-pre-wrap">{message.content}</div>
        ) : (
          <div className="flex flex-col gap-3">
            {message.thought && (
              <div className="text-muted-foreground italic border-l-2 border-primary/30 pl-4 py-1 text-[14px] bg-muted/30 rounded-r-md">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.thought.replace(/^Thought:\s*/, '')}
                </ReactMarkdown>
              </div>
            )}
            {message.content && (
              <div className="markdown-body prose max-w-none dark:prose-invert">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatBubble;
