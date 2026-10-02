const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_PREFIX = process.env.NEXT_PUBLIC_API_PREFIX || "/api/v1";

const BASE_URL = `${API_URL}${API_PREFIX}`;

// ============================
// Types
// ============================

export interface ChatRequest {
  message: string;
  session_id?: string;
  stream?: boolean;
}

export interface ChatResponse {
  reply: string;
  model: string;
  session_id: string;
  tokens_used?: number;
}

export interface AgentRequest {
  query: string;
  session_id?: string;
  user_id?: string;
}

export interface AgentResponse {
  response: string;
  agent_used: string;
  tool_used: string;
  supervisor_reasoning: string;
  session_id: string;
  user_id?: string;
  rag_sources: string[];
  has_rag_context: boolean;
  iterations: number;
  memory_backend?: string;
}

export interface IngestResponse {
  status: string;
  documents_loaded: number;
  chunks_created: number;
  files_processed: string[];
}

export interface ToolRegistryResponse {
  total_tools: number;
  total_agents: number;
  tools_per_agent: Record<string, number>;
  categories: Record<string, number>;
  tools: ToolInfo[];
}

export interface ToolInfo {
  name: string;
  description: string;
  agent: string;
  category: string;
  tags: string[];
  requires_context: boolean;
  requires_file: boolean;
}

export interface MemoryStatsResponse {
  backend: string;
  redis_connected: boolean;
  total_sessions: number;
  total_user_mappings: number;
  max_conversation_turns: number;
  ttl_seconds: number;
}

export interface SessionInfo {
  session_id: string;
  message_count: number;
  history: { role: string; content: string }[];
}

// ============================
// API Functions
// ============================

export async function sendChatMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) throw new Error(`Chat error: ${res.statusText}`);
  return res.json();
}

export async function runAgent(
  request: AgentRequest
): Promise<AgentResponse> {
  const res = await fetch(`${BASE_URL}/agent/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) throw new Error(`Agent error: ${res.statusText}`);
  return res.json();
}

export async function streamAgent(
  request: AgentRequest,
  onChunk: (content: string) => void,
  onComplete: (metadata: any) => void,
  onError: (error: string) => void,
): Promise<void> {
  try {
    const res = await fetch(`${BASE_URL}/agent/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    if (!res.ok) {
      onError(`Stream error: ${res.statusText}`);
      return;
    }

    const reader = res.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      onError("No reader available");
      return;
    }

    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data:")) {
          const data = line.slice(5).trim();
          if (!data) continue;

          try {
            const parsed = JSON.parse(data);

            if (parsed.content) {
              onChunk(parsed.content);
            }
          } catch {
            // Skip non-JSON data
          }
        }

        if (line.startsWith("event:")) {
          const eventType = line.slice(6).trim();
          if (eventType === "complete" || eventType === "error") {
            // Will be handled by next data line
          }
        }
      }
    }

    // Parse final buffer
    if (buffer) {
      try {
        const parsed = JSON.parse(buffer);
        onComplete(parsed);
      } catch {
        // Ignore
      }
    }
  } catch (err) {
    onError(err instanceof Error ? err.message : "Unknown stream error");
  }
}

export async function uploadFile(
  file: File
): Promise<{ filename: string; detected_type: string; message: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BASE_URL}/agent/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`Upload error: ${res.statusText}`);
  return res.json();
}

export async function getToolRegistry(): Promise<ToolRegistryResponse> {
  const res = await fetch(`${BASE_URL}/tools`);
  if (!res.ok) throw new Error(`Tools error: ${res.statusText}`);
  return res.json();
}

export async function getMemoryStats(): Promise<MemoryStatsResponse> {
  const res = await fetch(`${BASE_URL}/memory/stats`);
  if (!res.ok) throw new Error(`Memory stats error: ${res.statusText}`);
  return res.json();
}

export async function getSessionHistory(
  sessionId: string,
  userId?: string
): Promise<SessionInfo> {
  const params = new URLSearchParams();
  if (userId) params.set("user_id", userId);

  const res = await fetch(
    `${BASE_URL}/memory/session/${sessionId}?${params}`
  );
  if (!res.ok) throw new Error(`Session error: ${res.statusText}`);
  return res.json();
}

export async function clearSession(
  sessionId: string,
  userId?: string
): Promise<void> {
  const params = new URLSearchParams();
  if (userId) params.set("user_id", userId);

  await fetch(`${BASE_URL}/memory/session/${sessionId}?${params}`, {
    method: "DELETE",
  });
}

export async function checkHealth(): Promise<any> {
  const res = await fetch(`${API_URL}/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}