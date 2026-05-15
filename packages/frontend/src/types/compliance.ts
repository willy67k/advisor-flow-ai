/** Compliance queue API shapes — Step 7.1 (frontend). */

export interface ComplianceReport {
  readonly risk_level: string;
  readonly findings: readonly string[];
  readonly prohibited_hits?: readonly string[];
  readonly disclosure_gaps?: readonly string[];
}

export interface ComplianceInterruptPayload {
  readonly stage?: string;
  readonly summary: string;
  readonly action_items: readonly {
    readonly task: string;
    readonly owner?: string | null;
    readonly due?: string | null;
  }[];
  readonly compliance?: ComplianceReport;
}

export interface CompliancePendingItem {
  readonly workflow_id: number;
  readonly meeting_id: number;
  readonly meeting_title: string;
  readonly compliance_review: ComplianceInterruptPayload;
}

export interface ComplianceWorkflowActionResponse {
  readonly workflow_id: number;
  readonly status: string;
}
