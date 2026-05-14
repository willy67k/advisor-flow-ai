import { useEffect, useState } from "react";

import { fetchWorkflow } from "../../services/workflowsApi";
import type { Workflow, WorkflowStatus } from "../../types/workflows";

interface Node {
  readonly key: string;
  readonly label: string;
}

const NODES: Node[] = [
  { key: "start", label: "Start" },
  { key: "retrieve_context", label: "Retrieve Context" },
  { key: "generate_summary", label: "Generate Summary" },
  { key: "extract_action_items", label: "Extract Action Items" },
  { key: "compliance_check", label: "Compliance Check" },
  { key: "wait_for_approval", label: "Awaiting Approval" },
  { key: "end", label: "End" },
];

type NodeState = "done" | "active" | "waiting" | "failed" | "pending";

function resolveNodeStates(status: WorkflowStatus): Map {
  const m = new Map<string, NodeState>();

  const allKeys = NODES.map((n) => n.key);

  const markUpTo = (lastDone: string, activeKey?: string, failedKey?: string) => {
    let pastActive = false;
    for (const key of allKeys) {
      if (failedKey && key === failedKey) {
        m.set(key, "failed");
        pastActive = true;
        continue;
      }
      if (activeKey && key === activeKey) {
        m.set(key, "active");
        continue;
      }
      if (key === lastDone) {
        m.set(key, "done");
        continue;
      }
      if (pastActive) {
        m.set(key, "pending");
        continue;
      }
      const doneKeys = allKeys.slice(0, allKeys.indexOf(lastDone) + 1);
      m.set(key, doneKeys.includes(key) ? "done" : "pending");
    }
  };

  switch (status) {
    case "pending":
      for (const k of allKeys) m.set(k, k === "start" ? "active" : "pending");
      break;
    case "processing":
      m.set("start", "done");
      m.set("retrieve_context", "done");
      m.set("generate_summary", "active");
      m.set("extract_action_items", "pending");
      m.set("compliance_check", "pending");
      m.set("wait_for_approval", "pending");
      m.set("end", "pending");
      break;
    case "waiting_approval":
      m.set("start", "done");
      m.set("retrieve_context", "done");
      m.set("generate_summary", "done");
      m.set("extract_action_items", "done");
      m.set("compliance_check", "done");
      m.set("wait_for_approval", "active");
      m.set("end", "pending");
      break;
    case "completed":
      for (const k of allKeys) m.set(k, "done");
      break;
    case "failed":
      markUpTo("generate_summary", undefined, "generate_summary");
      m.set("start", "done");
      m.set("retrieve_context", "done");
      m.set("generate_summary", "failed");
      m.set("extract_action_items", "pending");
      m.set("compliance_check", "pending");
      m.set("wait_for_approval", "pending");
      m.set("end", "pending");
      break;
    case "rejected":
      m.set("start", "done");
      m.set("retrieve_context", "done");
      m.set("generate_summary", "done");
      m.set("extract_action_items", "done");
      m.set("compliance_check", "done");
      m.set("wait_for_approval", "failed");
      m.set("end", "pending");
      break;
    default:
      for (const k of allKeys) m.set(k, "pending");
  }
  return m;
}

const NODE_ICONS: Record = {
  done: (
    <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
      <path clipRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" fillRule="evenodd" />
    </svg>
  ),
  active: <span className="h-2 w-2 animate-pulse rounded-full bg-current" />,
  waiting: <span className="h-2 w-2 rounded-full bg-current" />,
  failed: (
    <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
      <path
        clipRule="evenodd"
        d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
        fillRule="evenodd"
      />
    </svg>
  ),
  pending: <span className="h-2 w-2 rounded-full bg-current" />,
};

const NODE_COLORS: Record = {
  done: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
  active: "bg-amber-500/20 text-amber-400 border-amber-500/40",
  waiting: "bg-slate-700/60 text-slate-400 border-slate-600",
  failed: "bg-rose-500/20 text-rose-400 border-rose-500/40",
  pending: "bg-slate-800/60 text-slate-600 border-slate-700/40",
};

const STATUS_BADGE: Record = {
  pending: "bg-slate-700 text-slate-300",
  processing: "bg-amber-500/20 text-amber-400",
  waiting_approval: "bg-blue-500/20 text-blue-400",
  completed: "bg-emerald-500/20 text-emerald-400",
  failed: "bg-rose-500/20 text-rose-400",
  rejected: "bg-rose-500/20 text-rose-400",
};

const STATUS_LABEL: Record = {
  pending: "Pending",
  processing: "Processing",
  waiting_approval: "Awaiting Approval",
  completed: "Completed",
  failed: "Failed",
  rejected: "Rejected",
};

interface Props {
  readonly workflowId: number;
  readonly poll?: boolean;
}

export function WorkflowTimeline({ workflowId, poll = true }: Props) {
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      const data = await fetchWorkflow(workflowId);
      setWorkflow(data);
      setError(null);
    } catch {
      setError("Unable to load workflow status.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [workflowId]);

  useEffect(() => {
    if (!poll || !workflow) return;
    const terminal = ["completed", "failed", "rejected"];
    if (terminal.includes(workflow.status)) return;

    const id = setInterval(() => void load(), 3000);
    return () => clearInterval(id);
  }, [poll, workflow]);

  if (loading) {
    return <p className="text-sm text-slate-500">Loading workflow…</p>;
  }

  if (error || !workflow) {
    return <p className="text-sm text-rose-400">{error ?? "Workflow not found."}</p>;
  }

  const nodeStates = resolveNodeStates(workflow.status);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <span className="text-xs font-medium text-slate-500">Workflow #{workflow.id}</span>
        <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${STATUS_BADGE[workflow.status]}`}>{STATUS_LABEL[workflow.status]}</span>
        {workflow.celery_state ? <span className="text-xs text-slate-600">({workflow.celery_state})</span> : null}
      </div>

      <div className="flex flex-wrap items-center gap-1">
        {NODES.map((node, idx) => {
          const state = nodeStates.get(node.key) ?? "pending";
          return (
            <div key={node.key} className="flex items-center gap-1">
              <div className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors ${NODE_COLORS[state]}`}>
                <span>{NODE_ICONS[state]}</span>
                <span>{node.label}</span>
              </div>
              {idx < NODES.length - 1 ? (
                <svg className="h-3 w-3 shrink-0 text-slate-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              ) : null}
            </div>
          );
        })}
      </div>

      {workflow.status === "completed" && workflow.result_json ? (
        <details className="rounded-lg border border-slate-800 bg-slate-900/40">
          <summary className="cursor-pointer px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-300">View result JSON</summary>
          <pre className="overflow-x-auto px-4 pb-4 text-xs text-slate-400">{JSON.stringify(workflow.result_json, null, 2)}</pre>
        </details>
      ) : null}
    </div>
  );
}
