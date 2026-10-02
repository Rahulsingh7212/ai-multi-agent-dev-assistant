"use client";

import { useChatStore } from "@/store/chat-store";
import { AgentSelector } from "./agent-selector";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Plus, Trash2, PanelLeftClose } from "lucide-react";

export function Sidebar() {
  const {
    sessionId,
    setSessionId,
    clearMessages,
    sidebarOpen,
    setSidebarOpen,
  } = useChatStore();

  const handleNewChat = () => {
    clearMessages();
    setSessionId(
      `session-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
    );
  };

  if (!sidebarOpen) return null;

  return (
    <div className="w-72 border-r bg-muted/30 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
            <span className="text-primary-foreground text-sm">🤖</span>
          </div>
          <div>
            <h2 className="text-sm font-semibold">Multi-Agent AI</h2>
            <p className="text-xs text-muted-foreground">Dev Assistant</p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setSidebarOpen(false)}
          className="h-8 w-8"
        >
          <PanelLeftClose className="h-4 w-4" />
        </Button>
      </div>

      <Separator />

      {/* New Chat Button */}
      <div className="p-3">
        <Button
          onClick={handleNewChat}
          variant="outline"
          className="w-full justify-start gap-2"
        >
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>

      <Separator />

      {/* Agent Selector */}
      <ScrollArea className="flex-1 p-3">
        <AgentSelector />
      </ScrollArea>

      <Separator />

      {/* Footer */}
      <div className="p-3 space-y-2">
        <div className="text-xs text-muted-foreground px-3">
          Session: {sessionId.slice(0, 16)}...
        </div>
        <Button
          onClick={() => {
            clearMessages();
          }}
          variant="ghost"
          size="sm"
          className="w-full justify-start gap-2 text-muted-foreground hover:text-destructive"
        >
          <Trash2 className="h-3 w-3" />
          Clear Chat
        </Button>
      </div>
    </div>
  );
}