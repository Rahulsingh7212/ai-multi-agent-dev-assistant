"use client";

import { useEffect, useRef } from "react";
import { useChatStore } from "@/store/chat-store";
import { ChatMessage } from "./chat-message";
import { ChatInput } from "./chat-input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Bot, PanelLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export function ChatContainer() {
  const { messages, sidebarOpen, setSidebarOpen, activeAgent } =
    useChatStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Header */}
      <div className="border-b px-4 py-3 flex items-center gap-3">
        {!sidebarOpen && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(true)}
            className="h-8 w-8"
          >
            <PanelLeft className="h-4 w-4" />
          </Button>
        )}
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-primary" />
          <h1 className="text-lg font-semibold">AI Dev Assistant</h1>
        </div>
        <div className="flex-1" />
        <div className="text-xs text-muted-foreground">
          {messages.length} message{messages.length !== 1 ? "s" : ""}
        </div>
      </div>

      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        {messages.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="max-w-3xl mx-auto space-y-1">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
          </div>
        )}
      </ScrollArea>

      {/* Input Area */}
      <div className="max-w-3xl mx-auto w-full">
        <ChatInput />
      </div>
    </div>
  );
}

function EmptyState() {
  const { activeAgent } = useChatStore();

  return (
    <div className="flex flex-col items-center justify-center h-full text-center py-20">
      <div className="h-16 w-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
        <span className="text-3xl">🤖</span>
      </div>
      <h2 className="text-xl font-semibold mb-2">
        AI Multi-Agent Developer Assistant
      </h2>
      <p className="text-muted-foreground max-w-md mb-8">
        Ask me to write code, analyze resumes, search GitHub, find information
        online, or answer questions from your documents.
      </p>

      <div className="grid grid-cols-2 gap-3 max-w-lg">
        {[
          { icon: "🧑‍💻", text: "Write a Python FastAPI endpoint", agent: "code_agent" },
          { icon: "📄", text: "Analyze my resume for senior roles", agent: "resume_agent" },
          { icon: "🐙", text: "Search trending AI repos on GitHub", agent: "github_agent" },
          { icon: "🌐", text: "What's new in Python 3.13?", agent: "web_agent" },
        ].map((suggestion, i) => (
          <button
            key={i}
            className="flex items-center gap-2 p-3 rounded-lg border hover:bg-accent text-sm text-left transition-colors"
          >
            <span className="text-lg">{suggestion.icon}</span>
            <span className="text-muted-foreground">{suggestion.text}</span>
          </button>
        ))}
      </div>
    </div>
  );
}