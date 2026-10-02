"use client";

import { useEffect, useRef, useState } from "react";
import {
  Bot,
  Code2,
  GitBranch,
  Globe,
  Send,
  User,
  Loader2,
  Plus,
  Trash2,
  FileText,
  Sparkles,
  Upload,
  Copy,
  Check,
} from "lucide-react";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

interface WebResult {
  title: string;
  url: string;
  content: string;
  score?: number | null;
  published_date?: string | null;
}

interface GitHubRepository {
  full_name: string;
  name: string;
  owner: string;
  description: string;
  stars: number;
  forks: number;
  language: string;
  open_issues: number;
  url: string;
  default_branch?: string;
  updated_at?: string | null;
  topics?: string[];
}

interface GitHubItem {
  number?: number;
  title?: string;
  state?: string;
  author?: string;
  labels?: string[];
  created_at?: string | null;
  updated_at?: string | null;
  comments?: number;
  review_comments?: number;
  head_branch?: string;
  base_branch?: string;
  url?: string;
}

interface GitHubResults {
  type?: string;
  query?: string;
  result_count?: number;
  repository?: GitHubRepository | null;
  results?: GitHubRepository[] | GitHubItem[];
  state?: string;
  error?: string;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string;
  webResults?: WebResult[];
  githubResults?: GitHubResults;
}

interface SessionItem {
  session_id: string;
  message_count: number;
  metadata?: Record<string, unknown>;
}

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState("");

  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(false);

  const [loading, setLoading] = useState(false);
  const [agent, setAgent] = useState("Supervisor");

  const loadSessions = async () => {
  setLoadingSessions(true);

  try {
    const response = await fetch(
      `${API_URL}/api/v1/agent/sessions`
    );

    if (!response.ok) {
      throw new Error(
        `Failed to load sessions: ${response.status}`
      );
    }

    const data = await response.json();

    if (Array.isArray(data.sessions)) {
      setSessions(data.sessions);
    } else {
      setSessions([]);
    }
  } catch (error) {
    console.error(
      "❌ Failed to load sessions:",
      error
    );
    setSessions([]);
  } finally {
    setLoadingSessions(false);
  }
};


const [selectedFile, setSelectedFile] = useState<File | null>(null);
const [uploadedFilename, setUploadedFilename] = useState("");
const [uploading, setUploading] = useState(false);
const [isDragging, setIsDragging] = useState(false);

const fileInputRef = useRef<HTMLInputElement>(null);


  const handleAgentClick = (selectedAgent: string) => {
  setAgent(selectedAgent);

  const prompts: Record<string, string> = {
    Supervisor: "Help me with my software development task",
    "Code Agent": "Generate a Python function",
    "Resume Agent": "Analyze my resume",
    "PDF Agent": "Summarize my document",
    "GitHub Agent": "Search GitHub for useful repositories",
    "Web Agent": "Search the web for the latest information",
  };

  setInput(prompts[selectedAgent] || "");
};

const uploadSelectedFile = async (file: File) => {
  setSelectedFile(file);
  setUploading(true);

  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(
      `${API_URL}/api/v1/agent/upload`,
      {
        method: "POST",
        body: formData,
      }
    );

    if (!response.ok) {
      throw new Error(
        `Upload failed: ${response.status} ${response.statusText}`
      );
    }

    const result = await response.json();

    setUploadedFilename(result.filename);

    if (agent === "Resume Agent") {
      setInput(
        "Analyze my uploaded resume and give me detailed feedback."
      );
    } else if (agent === "PDF Agent") {
      setInput(
        "Summarize my uploaded document and explain the key points."
      );
    }
  } catch (error) {
    console.error("File upload error:", error);

    setSelectedFile(null);
    setUploadedFilename("");

    const message =
      error instanceof Error
        ? error.message
        : "File upload failed.";

    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: "assistant",
        content: `❌ **File Upload Error**\n\n${message}`,
        agent: "System",
      },
    ]);
  } finally {
    setUploading(false);
    loadSessions();
  }
};

const handleFileUpload = async (
  event: React.ChangeEvent<HTMLInputElement>
) => {
  const file = event.target.files?.[0];

  if (!file) {
    return;
  }

  await uploadSelectedFile(file);

  // Allow selecting the same file again
  if (fileInputRef.current) {
    fileInputRef.current.value = "";
  }
};

const handleDragOver = (
  event: React.DragEvent<HTMLDivElement>
) => {
  event.preventDefault();
  event.stopPropagation();

  if (!uploading) {
    setIsDragging(true);
  }
};

const handleDragLeave = (
  event: React.DragEvent<HTMLDivElement>
) => {
  event.preventDefault();
  event.stopPropagation();

  setIsDragging(false);
};

const handleDrop = async (
  event: React.DragEvent<HTMLDivElement>
) => {
  event.preventDefault();
  event.stopPropagation();

  setIsDragging(false);

  if (uploading) {
    return;
  }

  const file = event.dataTransfer.files?.[0];

  if (!file) {
    return;
  }

  await uploadSelectedFile(file);
};

const copyToClipboard = async (text: string) => {
  try {
    await navigator.clipboard.writeText(text);
    console.log("✅ Copied to clipboard");
  } catch (error) {
    console.error("❌ Copy failed:", error);
  }
};

const processUploadedFile = async () => {
  if (!uploadedFilename) {
    return;
  }

  const query =
    input.trim() ||
    (agent === "Resume Agent"
      ? "Analyze my uploaded resume"
      : "Summarize my uploaded document");

  if (!sessionId || loading) {
    return;
  }

  setLoading(true);

  try {
    const params = new URLSearchParams({
      query,
      filename: uploadedFilename,
      session_id: sessionId,
    });

    const response = await fetch(
      `${API_URL}/api/v1/agent/run-with-file?${params.toString()}`,
      {
        method: "POST",
      }
    );

    if (!response.ok) {
      throw new Error(
        `File processing failed: ${response.status} ${response.statusText}`
      );
    }

    const result = await response.json();

    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: query,
      },
      {
        id: crypto.randomUUID(),
        role: "assistant",
        content:
          result.response ||
          "The file was processed, but no response was returned.",
        agent:
          result.agent_used ||
          (agent === "Resume Agent"
            ? "resume_agent"
            : "pdf_agent"),
      },
    ]);

    setInput("");
    setSelectedFile(null);
    setUploadedFilename("");
  } catch (error) {
    console.error("File processing error:", error);

    const message =
      error instanceof Error
        ? error.message
        : "File processing failed.";

    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: "assistant",
        content: `❌ **File Processing Error**\n\n${message}`,
        agent: "System",
      },
    ]);
  } finally {
    setLoading(false);
    
  }
};

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Create / restore session
  useEffect(() => {
    const storedSession = localStorage.getItem("ai-agent-session");

    if (storedSession) {
      setSessionId(storedSession);
    } else {
      const newSession = crypto.randomUUID();
      localStorage.setItem("ai-agent-session", newSession);
      setSessionId(newSession);
    }
  }, []);

useEffect(() => {
  loadSessions();
}, []);

  const loadSession = async (
  selectedSessionId: string
) => {
  if (!selectedSessionId) {
    return;
  }

  try {
    setLoading(true);

    const response = await fetch(
      `${API_URL}/api/v1/agent/session/${encodeURIComponent(
        selectedSessionId
      )}`
    );

    if (!response.ok) {
      throw new Error(
        `Failed to load session: ${response.status}`
      );
    }

    const data = await response.json();

    if (
      !data.history ||
      !Array.isArray(data.history)
    ) {
      return;
    }

    const restoredMessages: Message[] =
      data.history.map(
        (
          message: {
            role: string;
            content: string;
          },
          index: number
        ) => ({
          id: `session-${selectedSessionId}-${index}`,

          role:
            message.role === "human"
              ? "user"
              : "assistant",

          content:
            typeof message.content === "string"
              ? message.content
              : String(
                  message.content ?? ""
                ),

          agent:
            message.role === "human"
              ? undefined
              : "Assistant",
        })
      );

    localStorage.setItem(
      "ai-agent-session",
      selectedSessionId
    );

    setSessionId(selectedSessionId);
    setMessages(restoredMessages);
    setAgent("Supervisor");
    setInput("");
  } catch (error) {
    console.error(
      "❌ Failed to load selected session:",
      error
    );
  } finally {
    setLoading(false);
  }
};

  useEffect(() => {
  const loadChatHistory = async () => {
    if (!sessionId) {
      return;
    }

    try {
      const response = await fetch(
        `${API_URL}/api/v1/agent/session/${encodeURIComponent(sessionId)}`
      );

      if (response.status === 404) {
        // New session — nothing to restore
        return;
      }

      if (!response.ok) {
        throw new Error(
          `Failed to load session: ${response.status}`
        );
      }

      const data = await response.json();

      if (!data.history || !Array.isArray(data.history)) {
        return;
      }

      const restoredMessages: Message[] = data.history.map(
        (message: { role: string; content: string }, index: number) => ({
          id: `restored-${sessionId}-${index}`,
          role:
            message.role === "human"
              ? "user"
              : "assistant",
          content:
            typeof message.content === "string"
              ? message.content
              : String(message.content ?? ""),
          agent:
            message.role === "human"
              ? undefined
              : "Assistant",
        })
      );

      setMessages(restoredMessages);
    } catch (error) {
      console.error(
        "❌ Failed to restore chat history:",
        error
      );
    }
  };

  loadChatHistory();
}, [sessionId]);

  // Auto scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  const sendMessage = async () => {
    const query = input.trim();

    if (!query || loading) {
      return;
    }

    if (!sessionId) {
      return;
    }

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: query,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    setAgent("Supervisor");

    try {
      const response = await fetch(`${API_URL}/api/v1/agent/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({
  query,
  session_id: sessionId,
  selected_agent:
    agent === "Supervisor"
      ? null
      : agent === "Code Agent"
        ? "code_agent"
        : agent === "Resume Agent"
          ? "resume_agent"
          : agent === "PDF Agent"
            ? "pdf_agent"
            : agent === "GitHub Agent"
              ? "github_agent"
              : agent === "Web Agent"
                ? "web_agent"
                : null,
}),
      });

      if (!response.ok) {
        throw new Error(
          `Backend error: ${response.status} ${response.statusText}`
        );
      }

      if (!response.body) {
        throw new Error("No response body received from backend.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let assistantMessageId = crypto.randomUUID();

      setMessages((prev) => [
        ...prev,
        {
          id: assistantMessageId,
          role: "assistant",
          content: "",
          agent: "Supervisor",
        },
      ]);

      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();

        if (done) {
          break;
        }

        buffer += decoder.decode(value, {
          stream: true,
        });

        const events = buffer.split(/\r?\n\r?\n/);

        buffer = events.pop() || "";

        for (const eventBlock of events) {
          const lines = eventBlock.split(/\r?\n/);

          let eventName = "";
          let data = "";

          for (const line of lines) {
            if (line.startsWith("event:")) {
              eventName = line.slice(6).trim();
            }

            if (line.startsWith("data:")) {
              data += line.slice(5).trim();
            }
          }

          if (!data) {
            continue;
          }

          try {
            const parsed = JSON.parse(data);

            // Start event
            if (eventName === "start") {
              if (parsed.agent) {
                setAgent(parsed.agent);
              }
            }

            // Content chunk
            if (eventName === "chunk") {
              const chunk = parsed.content || "";

              setMessages((prev) =>
                prev.map((message) =>
                  message.id === assistantMessageId
                    ? {
                        ...message,
                        content: message.content + chunk,
                      }
                    : message
                )
              );
            }

            // Complete event
            if (eventName === "complete") {
  if (parsed.agent_used) {
    setAgent(parsed.agent_used);
  }

  setMessages((prev) =>
    prev.map((message) =>
      message.id === assistantMessageId
        ? {
            ...message,
            agent:
              parsed.agent_used ||
              message.agent ||
              "Supervisor",

            webResults:
              Array.isArray(parsed.web_results)
                ? parsed.web_results
                : [],

                githubResults:
  parsed.github_results &&
  typeof parsed.github_results === "object"
    ? parsed.github_results
    : undefined,
          }
        : message
    )
  );
}

            // Error event
            if (eventName === "error") {
              throw new Error(
                parsed.error || "Unknown streaming error"
              );
            }
          } catch (parseError) {
            console.warn(
              "Could not parse SSE event:",
              data,
              parseError
            );
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error);

      const errorMessage =
        error instanceof Error
          ? error.message
          : "Something went wrong.";

      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            `❌ **Connection Error**\n\n${errorMessage}\n\n` +
            `Make sure your FastAPI backend is running on port 8000.`,
          agent: "System",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const newChat = () => {
    const newSession = crypto.randomUUID();

    localStorage.setItem("ai-agent-session", newSession);

    setSessionId(newSession);
    setMessages([]);
    setAgent("Supervisor");
    setInput("");

    loadSessions();
  };

  const clearChat = () => {
    setMessages([]);
  };

  const agentIcon = (agentName?: string) => {
    const name = (agentName || "").toLowerCase();

    if (name.includes("code")) {
      return <Code2 className="h-4 w-4" />;
    }

    if (name.includes("github")) {
      return <GitBranch className="h-4 w-4" />;
    }

    if (name.includes("web")) {
      return <Globe className="h-4 w-4" />;
    }

    if (name.includes("pdf") || name.includes("resume")) {
      return <FileText className="h-4 w-4" />;
    }

    return <Bot className="h-4 w-4" />;
  };

  const isResumeMessage = (message: Message) => {
  return (
    message.role === "assistant" &&
    message.agent?.toLowerCase().includes("resume")
  );
};
const isPdfMessage = (message: Message) => {
  return (
    message.role === "assistant" &&
    message.agent?.toLowerCase().includes("pdf")
  );
};

const isWebMessage = (message: Message) => {
  return (
    message.role === "assistant" &&
    message.agent?.toLowerCase().includes("web")
  );
};

const isGitHubMessage = (message: Message) => {
  return (
    message.role === "assistant" &&
    message.agent?.toLowerCase().includes("github")
  );
};

  return (
    <div className="flex h-screen w-full bg-background">
      {/* ================= SIDEBAR ================= */}

      <aside className="hidden w-72 flex-col border-r bg-muted/20 md:flex">
        <div className="flex h-16 items-center gap-3 border-b px-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <Sparkles className="h-5 w-5" />
          </div>

          <div>
            <h1 className="font-semibold">
              AI Dev Assistant
            </h1>

            <p className="text-xs text-muted-foreground">
              Multi-Agent System
            </p>
          </div>
        </div>

        <div className="p-4">
          <Button
            onClick={newChat}
            className="w-full gap-2"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </Button>
        </div>

        <Separator />

        <ScrollArea className="flex-1 px-4 py-4">
          <div className="space-y-3">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Agents
            </p>

            <button 
                type="button"
                onClick={() => handleAgentClick("Supervisor")}
                className="w-full text-left flex items-center gap-3 rounded-lg p-3 transition hover:bg-muted/50"
                >
              <Bot className="h-4 w-4" />

              <div>
                <p className="text-sm font-medium">
                  Supervisor
                </p>

                <p className="text-xs text-muted-foreground">
                  Intelligent routing
                </p>
              </div>
            </button>

            <button 
                type="button"
                onClick={() => handleAgentClick("Code Agent")}
                className="w-full text-left flex items-center gap-3 rounded-lg p-3 transition hover:bg-muted/50"
                >
              <Code2 className="h-4 w-4 text-blue-500" />

              <div>
                <p className="text-sm font-medium">
                  Code Agent
                </p>

                <p className="text-xs text-muted-foreground">
                  Coding & debugging
                </p>
              </div>
            </button>

            {/* Resume Agent */}
<button
  type="button"
  onClick={() => handleAgentClick("Resume Agent")}
  className={`w-full text-left flex items-center gap-3 rounded-lg p-3 transition hover:bg-muted/50 ${
    agent === "Resume Agent"
      ? "border bg-background"
      : ""
  }`}
>
  <FileText className="h-4 w-4 text-green-500" />

  <div>
    <p className="text-sm font-medium">
      Resume Agent
    </p>

    <p className="text-xs text-muted-foreground">
      Resume analysis
    </p>
  </div>
</button>

{/* PDF Agent */}
<button
  type="button"
  onClick={() => handleAgentClick("PDF Agent")}
  className={`w-full text-left flex items-center gap-3 rounded-lg p-3 transition hover:bg-muted/50 ${
    agent === "PDF Agent"
      ? "border bg-background"
      : ""
  }`}
>
  <FileText className="h-4 w-4 text-orange-500" />

  <div>
    <p className="text-sm font-medium">
      PDF Agent
    </p>

    <p className="text-xs text-muted-foreground">
      Document analysis
    </p>
  </div>
</button>

{/* GitHub Agent */}
<button
  type="button"
  onClick={() => handleAgentClick("GitHub Agent")}
  className={`w-full text-left flex items-center gap-3 rounded-lg p-3 transition hover:bg-muted/50 ${
    agent === "GitHub Agent"
      ? "border bg-background"
      : ""
  }`}
>
  <GitBranch className="h-4 w-4" />

  <div>
    <p className="text-sm font-medium">
      GitHub Agent
    </p>

    <p className="text-xs text-muted-foreground">
      Repository operations
    </p>
  </div>
</button>

{/* Web Agent */}
<button
  type="button"
  onClick={() => handleAgentClick("Web Agent")}
  className={`w-full text-left flex items-center gap-3 rounded-lg p-3 transition hover:bg-muted/50 ${
    agent === "Web Agent"
      ? "border bg-background"
      : ""
  }`}
>
  <Globe className="h-4 w-4 text-purple-500" />

  <div>
    <p className="text-sm font-medium">
      Web Agent
    </p>

    <p className="text-xs text-muted-foreground">
      Web search & news
    </p>
  </div>
</button>


{(agent === "Resume Agent" || agent === "PDF Agent") && (
  <div className="mt-4 rounded-xl border bg-background p-3">
    <p className="mb-3 text-sm font-semibold">
      {agent === "Resume Agent"
        ? "Upload Resume"
        : "Upload PDF / Document"}
    </p>

    <input
      ref={fileInputRef}
      type="file"
      accept={
        agent === "Resume Agent"
          ? ".pdf,.txt,.doc,.docx"
          : ".pdf,.txt"
      }
      onChange={handleFileUpload}
      className="hidden"
    />

    {/* Drag & Drop Area */}
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => {
        if (!uploading) {
          fileInputRef.current?.click();
        }
      }}
      className={`cursor-pointer rounded-xl border-2 border-dashed p-5 text-center transition ${
        isDragging
          ? "border-primary bg-primary/10"
          : "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/30"
      }`}
    >
      <div className="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-full bg-primary/10">
        {uploading ? (
          <Loader2 className="h-5 w-5 animate-spin text-primary" />
        ) : (
          <Upload className="h-5 w-5 text-primary" />
        )}
      </div>

      {uploading ? (
        <>
          <p className="text-sm font-medium">
            Uploading file...
          </p>

          <p className="mt-1 text-xs text-muted-foreground">
            Please wait
          </p>
        </>
      ) : isDragging ? (
        <>
          <p className="text-sm font-medium text-primary">
            Drop your file here
          </p>

          <p className="mt-1 text-xs text-muted-foreground">
            Release to upload
          </p>
        </>
      ) : (
        <>
          <p className="text-sm font-medium">
            Drop your file here
          </p>

          <p className="my-1 text-xs text-muted-foreground">
            or
          </p>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={(event) => {
              event.stopPropagation();
              fileInputRef.current?.click();
            }}
            disabled={uploading}
          >
            Choose File
          </Button>

          <p className="mt-2 text-[11px] text-muted-foreground">
            {agent === "Resume Agent"
              ? "PDF, TXT, DOC, DOCX"
              : "PDF, TXT"}
          </p>
        </>
      )}
    </div>

    {/* Selected File */}
    {selectedFile && (
      <div className="mt-3 rounded-lg border bg-muted/30 p-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
            <FileText className="h-4 w-4 text-primary" />
          </div>

          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">
              {selectedFile.name}
            </p>

            <p className="text-xs text-muted-foreground">
              {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>

          {uploadedFilename && (
            <span className="shrink-0 text-xs font-medium text-green-500">
              ✓ Uploaded
            </span>
          )}
        </div>

        {uploadedFilename && (
          <Button
            type="button"
            className="mt-3 w-full"
            onClick={processUploadedFile}
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                {agent === "Resume Agent"
                  ? "Analyze Resume"
                  : "Analyze Document"}
              </>
            )}
          </Button>
        )}
      </div>
    )}
  </div>
)}
          </div>
        </ScrollArea>

        <div className="border-t p-4">
  <div className="rounded-lg bg-background p-3">
    <div className="mb-3 flex items-center justify-between">
      <p className="text-xs font-medium text-muted-foreground">
        Recent Sessions
      </p>

      <button
        type="button"
        onClick={loadSessions}
        className="text-xs text-muted-foreground hover:text-foreground"
      >
        Refresh
      </button>
    </div>

    {loadingSessions ? (
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <Loader2 className="h-3 w-3 animate-spin" />
        Loading sessions...
      </div>
    ) : sessions.length === 0 ? (
      <p className="text-xs text-muted-foreground">
        No previous sessions
      </p>
    ) : (
      <div className="max-h-52 space-y-1 overflow-y-auto">
        {sessions
          .filter(
            (session) =>
              session.session_id !== sessionId
          )
          .map((session) => (
            <button
              key={session.session_id}
              type="button"
              onClick={() =>
                loadSession(
                  session.session_id
                )
              }
              className="w-full rounded-md p-2 text-left transition hover:bg-muted"
            >
              <p className="truncate text-xs font-medium">
                {session.metadata &&
                typeof session.metadata ===
                  "object" &&
                "title" in session.metadata
                  ? String(
                      session.metadata.title
                    )
                  : `Session ${session.session_id.slice(
                      0,
                      8
                    )}`}
              </p>

              <p className="mt-1 text-[11px] text-muted-foreground">
                {session.message_count} messages
              </p>
            </button>
          ))}
      </div>
    )}
  </div>

  <div className="mt-2 rounded-lg bg-background p-3">
    <p className="text-xs text-muted-foreground">
      Current Session
    </p>

    <p className="mt-1 truncate font-mono text-xs">
      {sessionId || "Creating..."}
    </p>
  </div>
</div>
      </aside>

      {/* ================= MAIN ================= */}

      <main className="flex min-w-0 flex-1 flex-col">
        {/* Header */}

        <header className="flex h-16 items-center justify-between border-b px-4 md:px-6">
          <div>
            <h2 className="font-semibold">
              AI Coding Assistant
            </h2>

            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <span className="h-2 w-2 rounded-full bg-green-500" />
              Backend connected
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1">
              {agentIcon(agent)}
              {agent}
            </Badge>

            <Button
              variant="ghost"
              size="icon"
              onClick={clearChat}
              title="Clear chat"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </header>

        {/* Messages */}

        <ScrollArea className="flex-1">
          <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-4 py-8 md:px-6">
            {messages.length === 0 ? (
              <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
                <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
                  <Sparkles className="h-8 w-8 text-primary" />
                </div>

                <h2 className="text-3xl font-bold">
                  AI Multi-Agent Dev Assistant
                </h2>

                <p className="mt-3 max-w-xl text-muted-foreground">
                  Ask me to write code, debug problems, analyze
                  resumes, work with documents, search GitHub,
                  or find information on the web.
                </p>

                <div className="mt-8 grid w-full max-w-2xl grid-cols-1 gap-3 sm:grid-cols-2">
                  <Card
                    className="cursor-pointer transition hover:bg-muted/50"
                    onClick={() =>
                      setInput(
                        "Generate a Python function to fetch data from an API"
                      )
                    }
                  >
                    <CardContent className="p-4">
                      <Code2 className="mb-2 h-5 w-5" />

                      <p className="text-sm font-medium">
                        Generate Code
                      </p>

                      <p className="mt-1 text-xs text-muted-foreground">
                        Create functions and programs
                      </p>
                    </CardContent>
                  </Card>

                  <Card
                    className="cursor-pointer transition hover:bg-muted/50"
                    onClick={() =>
                      setInput(
                        "Explain how FastAPI works with Python"
                      )
                    }
                  >
                    <CardContent className="p-4">
                      <Bot className="mb-2 h-5 w-5" />

                      <p className="text-sm font-medium">
                        Explain Code
                      </p>

                      <p className="mt-1 text-xs text-muted-foreground">
                        Understand technical concepts
                      </p>
                    </CardContent>
                  </Card>

                  <Card
                    className="cursor-pointer transition hover:bg-muted/50"
                    onClick={() =>
                      setInput(
                        "Search GitHub for useful FastAPI projects"
                      )
                    }
                  >
                    <CardContent className="p-4">
                      <GitBranch className="mb-2 h-5 w-5" />

                      <p className="text-sm font-medium">
                        GitHub Search
                      </p>

                      <p className="mt-1 text-xs text-muted-foreground">
                        Find repositories and projects
                      </p>
                    </CardContent>
                  </Card>

                  <Card
                    className="cursor-pointer transition hover:bg-muted/50"
                    onClick={() =>
                      setInput(
                        "What are the latest developments in AI?"
                      )
                    }
                  >
                    <CardContent className="p-4">
                      <Globe className="mb-2 h-5 w-5" />

                      <p className="text-sm font-medium">
                        Web Search
                      </p>

                      <p className="mt-1 text-xs text-muted-foreground">
                        Search current information
                      </p>
                    </CardContent>
                  </Card>
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-4 ${
                    message.role === "user"
                      ? "justify-end"
                      : "justify-start"
                  }`}
                >
                  {message.role === "assistant" && (
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                      {agentIcon(message.agent)}
                    </div>
                  )}

                  <div
                    className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                      message.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "border bg-card"
                    }`}
                  >
                    {message.role === "assistant" &&
                      message.agent && (
                        <div className="mb-2 flex items-center gap-2">
                          <span className="text-xs font-medium text-muted-foreground">
                            {message.agent}
                          </span>
                        </div>
                      )}
                    {isResumeMessage(message) && (
                      <div className="mb-2 flex items-center gap-2">
                        <span className="text-xs font-medium text-muted-foreground">
                          Resume
                        </span>
                      </div>
                    )}

                    {isResumeMessage(message) && (
  <div className="mb-4 rounded-lg border bg-muted/20 p-3">
    <div className="flex items-center gap-2">
      <FileText className="h-4 w-4 text-green-500" />
      <div>
        <p className="text-sm font-semibold">
          Resume Analysis
        </p>
        <p className="text-xs text-muted-foreground">
          Resume Agent
        </p>
      </div>
    </div>
  </div>
)}

{isPdfMessage(message) && (
  <div className="mb-4 rounded-lg border bg-muted/20 p-3">
    <div className="flex items-center gap-2">
      <FileText className="h-4 w-4 text-orange-500" />

      <div>
        <p className="text-sm font-semibold">
          Document Analysis
        </p>

        <p className="text-xs text-muted-foreground">
          PDF Agent
        </p>
      </div>
    </div>
  </div>
)}

{isWebMessage(message) &&
  message.webResults &&
  message.webResults.length > 0 && (
    <div className="mb-4 space-y-3">
      <div className="flex items-center gap-2">
        <Globe className="h-4 w-4 text-purple-500" />

        <p className="text-sm font-semibold">
          Web Search Results
        </p>
      </div>

      {message.webResults.map(
        (result, index) => (
          <Card
            key={`${message.id}-web-${index}`}
            className="overflow-hidden border bg-background"
          >
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-purple-500/10">
                  <Globe className="h-4 w-4 text-purple-500" />
                </div>

                <div className="min-w-0 flex-1">
                  <h4 className="font-semibold leading-5">
                    {result.title || "Untitled Article"}
                  </h4>

                  <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    {result.published_date && (
                      <span>
                        {result.published_date}
                      </span>
                    )}

                    {typeof result.score === "number" && (
                      <span>
                        Relevance:{" "}
                        {(result.score * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>

                  {result.content && (
                    <p className="mt-2 line-clamp-4 text-sm text-muted-foreground">
                      {result.content}
                    </p>
                  )}

                  {result.url && (
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-3 inline-flex items-center gap-1 text-sm font-medium underline underline-offset-4"
                    >
                      Open Article ↗
                    </a>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )
      )}
    </div>
  )}

  {isGitHubMessage(message) &&
  message.githubResults && (
    <div className="mb-4 space-y-3">
      <div className="flex items-center gap-2">
        <GitBranch className="h-4 w-4" />

        <p className="text-sm font-semibold">
          GitHub Results
        </p>
      </div>

      {/* Repository list */}
      {message.githubResults.type === "repositories" &&
        Array.isArray(message.githubResults.results) && (
          <div className="space-y-3">
            {message.githubResults.results.map(
              (item, index) => {
                const repo =
                  item as GitHubRepository;

                return (
                  <Card
                    key={`${message.id}-repo-${index}`}
                    className="overflow-hidden border bg-background"
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted">
                          <GitBranch className="h-4 w-4" />
                        </div>

                        <div className="min-w-0 flex-1">
                          <h4 className="font-semibold">
                            {repo.full_name}
                          </h4>

                          <p className="mt-1 text-sm text-muted-foreground">
                            {repo.description}
                          </p>

                          <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
                            <span>
                              ⭐ {repo.stars}
                            </span>

                            <span>
                              🍴 {repo.forks}
                            </span>

                            <span>
                              🧑‍💻 {repo.language}
                            </span>

                            <span>
                              🐛 {repo.open_issues} issues
                            </span>
                          </div>

                          {repo.topics &&
                            repo.topics.length > 0 && (
                              <div className="mt-3 flex flex-wrap gap-1.5">
                                {repo.topics
                                  .slice(0, 6)
                                  .map((topic) => (
                                    <Badge
                                      key={topic}
                                      variant="secondary"
                                    >
                                      {topic}
                                    </Badge>
                                  ))}
                              </div>
                            )}

                          {repo.url && (
                            <a
                              href={repo.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="mt-3 inline-flex text-sm font-medium underline underline-offset-4"
                            >
                              View Repository ↗
                            </a>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              }
            )}
          </div>
        )}

      {/* Issues */}
      {message.githubResults.type === "issues" &&
        Array.isArray(message.githubResults.results) && (
          <div className="space-y-3">
            {message.githubResults.results.map(
              (item, index) => {
                const issue =
                  item as GitHubItem;

                return (
                  <Card
                    key={`${message.id}-issue-${index}`}
                    className="border bg-background"
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted">
                          <span className="text-sm">
                            🐛
                          </span>
                        </div>

                        <div className="min-w-0 flex-1">
                          <h4 className="font-semibold">
                            #{issue.number}{" "}
                            {issue.title}
                          </h4>

                          <p className="mt-1 text-xs text-muted-foreground">
                            {issue.state} •{" "}
                            {issue.author}
                          </p>

                          {issue.labels &&
                            issue.labels.length > 0 && (
                              <div className="mt-2 flex flex-wrap gap-1.5">
                                {issue.labels.map(
                                  (label) => (
                                    <Badge
                                      key={label}
                                      variant="secondary"
                                    >
                                      {label}
                                    </Badge>
                                  )
                                )}
                              </div>
                            )}

                          <p className="mt-2 text-xs text-muted-foreground">
                            Comments:{" "}
                            {issue.comments ?? 0}
                          </p>

                          {issue.url && (
                            <a
                              href={issue.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="mt-3 inline-flex text-sm font-medium underline underline-offset-4"
                            >
                              View Issue ↗
                            </a>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              }
            )}
          </div>
        )}

      {/* Pull Requests */}
      {message.githubResults.type ===
        "pull_requests" &&
        Array.isArray(message.githubResults.results) && (
          <div className="space-y-3">
            {message.githubResults.results.map(
              (item, index) => {
                const pr =
                  item as GitHubItem;

                return (
                  <Card
                    key={`${message.id}-pr-${index}`}
                    className="border bg-background"
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted">
                          <span className="text-sm">
                            🔀
                          </span>
                        </div>

                        <div className="min-w-0 flex-1">
                          <h4 className="font-semibold">
                            #{pr.number}{" "}
                            {pr.title}
                          </h4>

                          <p className="mt-1 text-xs text-muted-foreground">
                            {pr.state} •{" "}
                            {pr.author}
                          </p>

                          {(pr.head_branch ||
                            pr.base_branch) && (
                            <p className="mt-2 text-xs text-muted-foreground">
                              {pr.head_branch} →
                              {" "}
                              {pr.base_branch}
                            </p>
                          )}

                          <p className="mt-2 text-xs text-muted-foreground">
                            Comments:{" "}
                            {pr.comments ?? 0}
                            {" • "}
                            Reviews:{" "}
                            {pr.review_comments ?? 0}
                          </p>

                          {pr.url && (
                            <a
                              href={pr.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="mt-3 inline-flex text-sm font-medium underline underline-offset-4"
                            >
                              View Pull Request ↗
                            </a>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              }
            )}
          </div>
        )}

      {/* Single repository */}
      {message.githubResults.type === "repository" &&
        message.githubResults.repository && (
          <Card className="border bg-background">
            <CardContent className="p-4">
              <h4 className="font-semibold">
                {message.githubResults.repository.full_name}
              </h4>

              <p className="mt-1 text-sm text-muted-foreground">
                {message.githubResults.repository.description}
              </p>

              <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted-foreground">
                <span>
                  ⭐{" "}
                  {message.githubResults.repository.stars}
                </span>

                <span>
                  🍴{" "}
                  {message.githubResults.repository.forks}
                </span>

                <span>
                  🧑‍💻{" "}
                  {message.githubResults.repository.language}
                </span>
              </div>

              {message.githubResults.repository.url && (
                <a
                  href={
                    message.githubResults.repository.url
                  }
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-3 inline-flex text-sm font-medium underline underline-offset-4"
                >
                  View Repository ↗
                </a>
              )}
            </CardContent>
          </Card>
        )}
    </div>
  )}

                    <div className="text-sm leading-6">
                      
  {message.content ? (
    message.role === "assistant" ? (
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => (
            <p className="mb-3 last:mb-0">
              {children}
            </p>
          ),

          ul: ({ children }) => (
            <ul className="mb-3 list-disc space-y-1 pl-5">
              {children}
            </ul>
          ),

          ol: ({ children }) => (
            <ol className="mb-3 list-decimal space-y-1 pl-5">
              {children}
            </ol>
          ),

          h1: ({ children }) => (
            <h1 className="mb-3 text-xl font-bold">
              {children}
            </h1>
          ),

          h2: ({ children }) => (
            <h2 className="mb-3 text-lg font-bold">
              {children}
            </h2>
          ),

          h3: ({ children }) => (
            <h3 className="mb-2 font-semibold">
              {children}
            </h3>
          ),

          blockquote: ({ children }) => (
            <blockquote className="my-3 border-l-2 pl-4 italic text-muted-foreground">
              {children}
            </blockquote>
          ),

          code: ({
            className,
            children,
            ...props
          }) => {
            const match = /language-(\w+)/.exec(
              className || ""
            );

            const codeText = String(children).replace(
              /\n$/,
              ""
            );

            // Fenced code block
            if (match) {
              return (
                <div className="my-4 overflow-hidden rounded-lg border bg-muted/30">
                  <div className="flex items-center justify-between border-b px-3 py-2">
                    <span className="text-xs font-medium text-muted-foreground">
                      {match[1]}
                    </span>

                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="h-7 gap-1"
                      onClick={() =>
                        copyToClipboard(codeText)
                      }
                    >
                      <Copy className="h-3.5 w-3.5" />
                      Copy
                    </Button>
                  </div>

                  <pre className="overflow-x-auto p-4 text-sm">
                    <code className={className} {...props}>
                      {children}
                    </code>
                  </pre>
                </div>
              );
            }

            // Inline code
            return (
              <code
                className="rounded bg-muted px-1.5 py-0.5 font-mono text-[0.9em]"
                {...props}
              >
                {children}
              </code>
            );
          },

          a: ({ children, href }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium underline underline-offset-4"
            >
              {children}
            </a>
          ),
        }}
      >
        {message.content}
      </ReactMarkdown>
    ) : (
      <div className="whitespace-pre-wrap">
        {message.content}
      </div>
    )
  ) : loading &&
    message.id ===
      messages[messages.length - 1]?.id ? (
    <Loader2 className="h-4 w-4 animate-spin" />
  ) : (
    ""
  )}
</div>
                  </div>

                  {message.role === "user" && (
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-muted">
                      <User className="h-4 w-4" />
                    </div>
                  )}
                </div>
              ))
            )}

            <div ref={messagesEndRef} />
          </div>
        </ScrollArea>

        {/* Input */}

        <div className="border-t bg-background p-4">
          <div className="mx-auto max-w-4xl">
            <div className="relative rounded-2xl border bg-muted/20 p-2 shadow-sm">
              <Textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask your AI development assistant..."
                disabled={loading}
                className="min-h-[60px] resize-none border-0 bg-transparent pr-14 shadow-none focus-visible:ring-0"
              />

              <Button
                onClick={sendMessage}
                disabled={!input.trim() || loading}
                size="icon"
                className="absolute bottom-3 right-3 h-9 w-9 rounded-xl"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>

            <p className="mt-2 text-center text-xs text-muted-foreground">
              Press Enter to send • Shift + Enter for a new line
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}