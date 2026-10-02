"use client";

import { Message } from "@/store/chat-store";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Bot, User, Wrench, Brain, Loader2 } from "lucide-react";

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isHuman = message.role === "human";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className="flex justify-center py-2">
        <span className="text-xs text-muted-foreground bg-muted px-3 py-1 rounded-full">
          {message.content}
        </span>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex gap-3 py-4",
        isHuman ? "flex-row" : "flex-row"
      )}
    >
      {/* Avatar */}
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback
          className={cn(
            "text-xs",
            isHuman
              ? "bg-blue-500 text-white"
              : "bg-purple-500 text-white"
          )}
        >
          {isHuman ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>

      {/* Content */}
      <div className="flex-1 space-y-2">
        {/* Header */}
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">
            {isHuman ? "You" : "AI Assistant"}
          </span>

          {!isHuman && message.agentUsed && (
            <Badge variant="secondary" className="text-xs gap-1">
              {message.agentUsed === "code_agent" && "🧑‍💻"}
              {message.agentUsed === "resume_agent" && "📄"}
              {message.agentUsed === "pdf_agent" && "📑"}
              {message.agentUsed === "github_agent" && "🐙"}
              {message.agentUsed === "web_agent" && "🌐"}
              {message.agentUsed}
            </Badge>
          )}

          {!isHuman && message.toolUsed && (
            <Badge variant="outline" className="text-xs gap-1">
              <Wrench className="h-2.5 w-2.5" />
              {message.toolUsed}
            </Badge>
          )}

          {message.isStreaming && (
            <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
          )}
        </div>

        {/* Supervisor Reasoning */}
        {!isHuman && message.supervisorReasoning && (
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Brain className="h-3 w-3" />
            <span>{message.supervisorReasoning}</span>
          </div>
        )}

        {/* Message Content */}
        <div
          className={cn(
            "prose prose-sm dark:prose-invert max-w-none",
            isHuman
              ? "bg-blue-500/10 rounded-lg p-3"
              : "bg-muted/50 rounded-lg p-3"
          )}
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>

        {/* RAG Sources */}
        {!isHuman && message.ragSources && message.ragSources.length > 0 && (
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <span>📚 Sources:</span>
            {message.ragSources.map((source, i) => (
              <Badge key={i} variant="outline" className="text-xs">
                {source}
              </Badge>
            ))}
          </div>
        )}

        {/* Timestamp */}
        <div className="text-xs text-muted-foreground">
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}