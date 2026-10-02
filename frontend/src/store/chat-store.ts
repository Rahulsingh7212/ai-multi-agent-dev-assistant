import { create } from "zustand";

// ============================
// Types
// ============================

export interface Message {
  id: string;
  role: "human" | "ai" | "system";
  content: string;
  agentUsed?: string;
  toolUsed?: string;
  supervisorReasoning?: string;
  ragSources?: string[];
  timestamp: Date;
  isStreaming?: boolean;
}

export type AgentType =
  | "auto"
  | "code_agent"
  | "resume_agent"
  | "pdf_agent"
  | "github_agent"
  | "web_agent";

export interface AgentInfo {
  id: AgentType;
  name: string;
  icon: string;
  description: string;
  color: string;
}

// ============================
// Agent Definitions
// ============================

export const AGENTS: AgentInfo[] = [
  {
    id: "auto",
    name: "Auto (Supervisor)",
    icon: "🤖",
    description: "Supervisor auto-routes to the best agent",
    color: "bg-purple-500",
  },
  {
    id: "code_agent",
    name: "Code Agent",
    icon: "🧑‍💻",
    description: "Generate, debug, explain, execute code",
    color: "bg-blue-500",
  },
  {
    id: "resume_agent",
    name: "Resume Agent",
    icon: "📄",
    description: "Parse, analyze, improve resumes",
    color: "bg-green-500",
  },
  {
    id: "pdf_agent",
    name: "PDF Agent",
    icon: "📑",
    description: "Document Q&A, summarize, compare",
    color: "bg-orange-500",
  },
  {
    id: "github_agent",
    name: "GitHub Agent",
    icon: "🐙",
    description: "Search repos, issues, pull requests",
    color: "bg-gray-700",
  },
  {
    id: "web_agent",
    name: "Web Agent",
    icon: "🌐",
    description: "Web search, real-time info, news",
    color: "bg-cyan-500",
  },
];

// ============================
// Store
// ============================

interface ChatState {
  // Messages
  messages: Message[];
  addMessage: (message: Message) => void;
  updateLastMessage: (content: string) => void;
  clearMessages: () => void;

  // Active agent
  activeAgent: AgentType;
  setActiveAgent: (agent: AgentType) => void;

  // Session
  sessionId: string;
  setSessionId: (id: string) => void;

  // User
  userId: string;
  setUserId: (id: string) => void;

  // UI State
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;

  // Uploaded file
  uploadedFileName: string | null;
  setUploadedFileName: (name: string | null) => void;

  // Error
  error: string | null;
  setError: (error: string | null) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  // Messages
  messages: [],
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  updateLastMessage: (content) =>
    set((state) => {
      const messages = [...state.messages];
      const last = messages[messages.length - 1];
      if (last) {
        messages[messages.length - 1] = {
          ...last,
          content: last.content + content,
          isStreaming: true,
        };
      }
      return { messages };
    }),
  clearMessages: () => set({ messages: [] }),

  // Active agent
  activeAgent: "auto",
  setActiveAgent: (agent) => set({ activeAgent: agent }),

  // Session
  sessionId: generateId(),
  setSessionId: (id) => set({ sessionId: id }),

  // User
  userId: "",
  setUserId: (id) => set({ userId: id }),

  // UI State
  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),
  sidebarOpen: true,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  // Uploaded file
  uploadedFileName: null,
  setUploadedFileName: (name) => set({ uploadedFileName: name }),

  // Error
  error: null,
  setError: (error) => set({ error }),
}));

function generateId(): string {
  return `session-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}