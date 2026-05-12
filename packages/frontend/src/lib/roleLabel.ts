/** Human-readable RBAC label from API (e.g. `compliance_officer` → `Compliance Officer`). */
export function roleLabel(role: string): string {
  return role
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");
}
