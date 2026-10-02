"use client";

import { useChatStore, AGENTS, AgentType } from "@/store/chat-store";
import { cn } from "@/lib/utils";
import {
  Bot,
  Code,
  FileText,
  FileSpreadsheet,
  GitBranch,
  Globe,
  Zap,
} from "lucide-react";

const agentIcons: Record<AgentType, React.ReactNode> = {
  auto: <Zap className="h-4 w-4" />,
  code_agent: <Code className="h-4 w-4" />,
  resume_agent: <FileText className="h-4 w-4" />,
  pdf_agent: <FileSpreadsheet className="h-4 w-4" />,
  github_agent: <GitBranch className="h-4 w-4" />,
  web_agent: <Globe className="h-4 w-4" />,
};

export function AgentSelector() {
  const { activeAgent, setActiveAgent } = useChatStore();

  return (
    <div className="space-y-1">
      <h3 className="px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        Select Agent
      </h3>

      <div className="space-y-1">
        {AGENTS.map((agent) => (
          <button
            key={agent.id}
            type="button"
            onClick={() => setActiveAgent(agent.id)}
            className={cn(
              "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all",
              "hover:bg-accent hover:text-accent-foreground",
              activeAgent === agent.id
                ? "bg-accent font-medium text-accent-foreground"
                : "text-muted-foreground"
            )}
          >
            <span className="flex h-5 w-5 shrink-0 items-center justify-center">
              {agentIcons[agent.id]}
            </span>

            <div className="min-w-0 flex-1 text-left">
              <div className="font-medium">
                {agent.name}
              </div>

              <div className="truncate text-xs text-muted-foreground">
                {agent.description}
              </div>
            </div>

            {activeAgent === agent.id && (
              <div className="h-2 w-2 shrink-0 animate-pulse rounded-full bg-primary" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
}