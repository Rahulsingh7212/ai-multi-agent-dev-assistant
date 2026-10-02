"use client";

import { useState, useRef, KeyboardEvent } from "react";
import { useChatStore } from "@/store/chat-store";
import { runAgent, streamAgent } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { FileUpload } from "./file-upload";
import { Send, Loader2, Sparkles } from "lucide-react";

interface ChatInputProps {
  onFileUploaded?: (filename: string, detectedType: string) => void;
}

export function ChatInput({ onFileUploaded }: ChatInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const {
    addMessage,
    updateLastMessage,
    activeAgent,
    sessionId,
    userId,
    isLoading,
    setIsLoading,
    uploadedFileName,
    setError,
  } = useChatStore();

  const handleSubmit = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput("");

    // Add user message
    addMessage({
      id: `msg-${Date.now()}`,
      role: "human",
      content: userMessage,
      timestamp: new Date(),
    });

    // Add placeholder AI message for streaming
    const aiMessageId = `msg-${Date.now() + 1}`;
    addMessage({
      id: aiMessageId,
      role: "ai",
      content: "",
      isStreaming: true,
      timestamp: new Date(),
    });

    setIsLoading(true);
    setError(null);

    try {
      // Build query with agent prefix if not auto
      let query = userMessage;
      if (activeAgent !== "auto") {
        // The supervisor will handle routing, but we can hint
        // by keeping the query as-is and letting the backend decide
      }

      if (uploadedFileName) {
        query += `\n[Attached file: ${uploadedFileName}]`;
      }

      // Try streaming first, fallback to regular
      await streamAgent(
        {
          query,
          session_id: sessionId,
          user_id: userId || undefined,
        },
        // onChunk
        (chunk) => {
          updateLastMessage(chunk);
        },
        // onComplete
        (metadata) => {
          // Update the last message with metadata
          const store = useChatStore.getState();
          const messages = [...store.messages];
          const last = messages[messages.length - 1];
          if (last && last.role === "ai") {
            messages[messages.length - 1] = {
              ...last,
              isStreaming: false,
              agentUsed: metadata.agent_used,
              toolUsed: metadata.tool_used,
              supervisorReasoning: metadata.supervisor_reasoning,
            };
            useChatStore.setState({ messages });
          }
          setIsLoading(false);
        },
        // onError
        (error) => {
          setError(error);
          setIsLoading(false);
          // Fallback to non-streaming
          fallbackToRegular(query);
        }
      );
    } catch (err) {
      // Fallback to regular request
      await fallbackToRegular(userMessage);
    }
  };

  const fallbackToRegular = async (query: string) => {
    try {
      const result = await runAgent({
        query,
        session_id: sessionId,
        user_id: userId || undefined,
      });

      // Replace streaming message with full response
      const store = useChatStore.getState();
      const messages = [...store.messages];
      const last = messages[messages.length - 1];
      if (last && last.role === "ai") {
        messages[messages.length - 1] = {
          ...last,
          content: result.response,
          isStreaming: false,
          agentUsed: result.agent_used,
          toolUsed: result.tool_used,
          supervisorReasoning: result.supervisor_reasoning,
          ragSources: result.rag_sources,
        };
        useChatStore.setState({ messages });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t bg-background p-4 space-y-3">
      {/* File Upload Area */}
      <FileUpload onFileUploaded={onFileUploaded} />

      {/* Input Area */}
      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              activeAgent === "auto"
                ? "Ask anything... (Supervisor will route to the best agent)"
                : `Ask the ${activeAgent.replace("_", " ")}...`
            }
            className="min-h-[60px] max-h-[200px] resize-none pr-12"
            disabled={isLoading}
          />
          <div className="absolute bottom-2 right-2 flex items-center gap-1">
            {activeAgent !== "auto" && (
              <span className="text-xs text-muted-foreground mr-2">
                {activeAgent === "code_agent" && "🧑‍💻"}
                {activeAgent === "resume_agent" && "📄"}
                {activeAgent === "pdf_agent" && "📑"}
                {activeAgent === "github_agent" && "🐙"}
                {activeAgent === "web_agent" && "🌐"}
              </span>
            )}
          </div>
        </div>

        <Button
          onClick={handleSubmit}
          disabled={!input.trim() || isLoading}
          size="icon"
          className="h-[60px] w-[60px]"
        >
          {isLoading ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Send className="h-5 w-5" />
          )}
        </Button>
      </div>

      {/* Agent indicator */}
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Sparkles className="h-3 w-3" />
        <span>
          {activeAgent === "auto"
            ? "Auto-routing enabled — Supervisor picks the best agent"
            : `Direct mode — ${activeAgent.replace("_", " ")}`}
        </span>
      </div>
    </div>
  );
}