import { type ReactNode, useCallback, useEffect, useState } from "react";

import { fetchWorkflow } from "../../services/workflowsApi";
import type { Workflow, WorkflowStatus } from "../../types/workflows";

interface Node {
  readonly key: string;
  readonly label: string;
}

const NODES: Node[] = [
  { key: "start", label: "Start" },
  { key: "retrieve_context", label: "Retrieve context" },
  { key: "generate_summary", label: "Generate summary" },
  { key: "extract_action_items", label: "Action items" },
  { key: "compliance_check", label: "Compliance scan" },
  { key: "wait_for_compliance", label: "Compliance review" },
  { key: "wait_for_advisor_approval", label: "Advisor approval" },
  { key: "end", label: "Done" },
];

type NodeState = "done" | "active" | "waiting" | "failed" | "pending";

function resolveNodeStates(status: WorkflowStatus, resultJson: Record<string, unknown> | null): Map<string, NodeState> {
  const m = new Map<string, NodeState>();
  const keys = NODES.map((n) => n.key);

  const fillDoneThrough = (lastDoneKey: string) => {
    const cut = keys.indexOf(lastDoneKey);
    for (let i = 0; i < keys.length; i++) {
      m.set(keys[i], i <= cut ? "done" : "pending");
    }
  };

  switch (status) {
    case "pending":
      for (const k of keys) {
        m.set(k, k === "start" ? "active" : "pending");
      }
      break;
    case "processing": {
      m.set("start", "done");
      m.set("retrieve_context", "done");
      m.set("generate_summary", "active");
      for (const k of keys) {
        if (!m.has(k)) {
          m.set(k, "pending");
        }
      }
      break;
    }
    case "waiting_compliance":
      fillDoneThrough("compliance_check");
      m.set("wait_for_compliance", "active");
      m.set("wait_for_advisor_approval", "pending");
      m.set("end", "pending");
      break;
    case "waiting_approval":
      fillDoneThrough("wait_for_compliance");
      m.set("wait_for_advisor_approval", "active");
      m.set("end", "pending");
      break;
    case "completed":
      for (const k of keys) {
        m.set(k, "done");
      }
      break;
    case "failed": {
      m.set("start", "done");
      m.set("retrieve_context", "done");
      m.set("generate_summary", "failed");
      for (const k of keys) {
        if (!m.has(k)) {
          m.set(k, "pending");
        }
      }
      break;
    }
    case "rejected": {
      const complianceRejected = Boolean(resultJson?.compliance_rejected);
      fillDoneThrough("compliance_check");
      if (complianceRejected) {
        m.set("wait_for_compliance", "failed");
        m.set("wait_for_advisor_approval", "pending");
      } else {
        m.set("wait_for_compliance", "done");
        m.set("wait_for_advisor_approval", "failed");
      }
      m.set("end", "pending");
      break;
    }
    default:
      for (const k of keys) {
        m.set(k, "pending");
      }
  }
  return m;
}

const NODE_ICONS: Record<NodeState, ReactNode> = {
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

const NODE_COLORS: Record<NodeState, string> = {
  done: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
  active: "bg-amber-500/20 text-amber-400 border-amber-500/40",
  waiting: "bg-slate-700/60 text-slate-400 border-slate-600",
  failed: "bg-rose-500/20 text-rose-400 border-rose-500/40",
  pending: "bg-slate-800/60 text-slate-600 border-slate-700/40",
};

const STATUS_BADGE: Record<WorkflowStatus, string> = {
  pending: "bg-slate-700 text-slate-300",
  processing: "bg-amber-500/20 text-amber-400",
  waiting_compliance: "bg-violet-500/20 text-violet-300",
  waiting_approval: "bg-blue-500/20 text-blue-400",
  completed: "bg-emerald-500/20 text-emerald-400",
  failed: "bg-rose-500/20 text-rose-400",
  rejected: "bg-rose-500/20 text-rose-400",
};

const STATUS_LABEL: Record<WorkflowStatus, string> = {
  pending: "Pending",
  processing: "Processing",
  waiting_compliance: "Awaiting compliance",
  waiting_approval: "Awaiting advisor approval",
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

  useEffect(() => {
    setLoading(true);
  }, [workflowId]);

  const load = useCallback(async () => {
    try {
      const data = await fetchWorkflow(workflowId);
      setWorkflow(data);
      setError(null);
    } catch {
      setError("Unable to load workflow status.");
    } finally {
      setLoading(false);
    }
  }, [workflowId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!poll || !workflow) {
      return;
    }
    const terminal: WorkflowStatus[] = ["completed", "failed", "rejected"];
    if (terminal.includes(workflow.status)) {
      return;
    }

    const id = setInterval(() => void load(), 3000);
    return () => clearInterval(id);
  }, [poll, workflow, load]);

  if (loading) {
    return <p className="text-sm text-slate-500">Loading workflow…</p>;
  }

  if (error || !workflow) {
    return <p className="text-sm text-rose-400">{error ?? "Workflow not found."}</p>;
  }

  const resultJson = workflow.result_json && typeof workflow.result_json === "object" ? (workflow.result_json as Record<string, unknown>) : null;
  const nodeStates = resolveNodeStates(workflow.status, resultJson);
  const complianceRejected = workflow.status === "rejected" && Boolean(resultJson?.compliance_rejected);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <span className="text-xs font-medium text-slate-500">Workflow #{workflow.id}</span>
        <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${STATUS_BADGE[workflow.status]}`}>{STATUS_LABEL[workflow.status]}</span>
        {workflow.celery_state ? <span className="text-xs text-slate-600">({workflow.celery_state})</span> : null}
      </div>

      {workflow.status === "waiting_compliance" ? (
        <div className="rounded-lg border border-violet-500/35 bg-violet-950/35 px-4 py-3 text-sm leading-relaxed text-violet-100">
          <p className="font-medium text-violet-200">Compliance review required</p>
          <p className="mt-1 text-violet-100/90">This draft scored high risk. A user with the compliance role must clear or reject it from the Compliance reviews page before you can approve it here.</p>
        </div>
      ) : null}

      {complianceRejected ? (
        <div className="rounded-lg border border-rose-500/40 bg-rose-950/30 px-4 py-3 text-sm leading-relaxed text-rose-100">
          <p className="font-medium text-rose-200">Closed at compliance</p>
          <p className="mt-1 text-rose-100/90">Compliance rejected this workflow. Review notes on the meeting page if provided, revise source notes or drafts, and start a new summary run when ready.</p>
        </div>
      ) : null}

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
