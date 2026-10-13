export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const leadStatuses = ["New", "Qualified", "Contacted", "Replied", "Won", "Lost"] as const;
export type LeadStatus = (typeof leadStatuses)[number];

export type Lead = {
  id: number;
  company_name: string;
  website: string;
  contact_name: string;
  email: string | null;
  industry: string;
  source: string;
  status: LeadStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

export type DashboardSummary = {
  total_leads: number;
  new_leads: number;
  qualified_prospects: number;
  follow_ups_pending: number;
  recent_leads: Lead[];
};

export type LeadPayload = Omit<Lead, "id" | "created_at" | "updated_at">;

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = Array.isArray(body?.detail)
      ? body.detail.map((item: { msg?: string }) => item.msg).join(" ")
      : body?.detail;
    throw new Error(detail || "Something went wrong. Please try again.");
  }

  return response.status === 204 ? (undefined as T) : response.json();
}

export const api = {
  getLeads: (search = "", status = "", industry = "") => {
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    if (status) params.set("status", status);
    if (industry) params.set("industry", industry);
    const query = params.toString();
    return request<{ items: Lead[]; industries: string[] }>(`/api/leads${query ? `?${query}` : ""}`);
  },
  getSummary: () => request<DashboardSummary>("/api/dashboard/summary"),
  createLead: (payload: LeadPayload) => request<Lead>("/api/leads", { method: "POST", body: JSON.stringify(payload) }),
  updateLead: (leadId: number, payload: Partial<LeadPayload>) =>
    request<Lead>(`/api/leads/${leadId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  updateStatus: (leadId: number, status: LeadStatus) =>
    request<Lead>(`/api/leads/${leadId}/status`, { method: "PATCH", body: JSON.stringify({ status }) }),
  deleteLead: (leadId: number) => request<void>(`/api/leads/${leadId}`, { method: "DELETE" }),
};
