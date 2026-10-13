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

export type UserProfile = {
  id: number;
  email: string;
  name: string;
  role: string;
  plan: string;
  token: string;
};

export type ProviderConnection = {
  provider: string;
  name: string;
  connection_method: "api_key" | "oauth" | "local" | null;
  status: "connected" | "error" | "expired" | "disconnected";
  status_message: string | null;
  selected_model: string;
  available_models: string[];
  base_url: string | null;
  key_preview: string | null;
  supports_oauth: boolean;
  supports_api_key: boolean;
  is_oauth_configured: boolean;
  oauth_limitation: string | null;
  is_default: boolean;
  updated_at: string | null;
};

export type TestConnectionResponse = {
  success: boolean;
  message: string;
  models: string[];
};

export type AISettings = {
  default_provider: string | null;
  default_model: string | null;
};

export type TestGenerateResponse = {
  response: string;
  provider: string;
  model: string;
};

let inMemoryToken: string | null = null;

export function setSessionToken(token: string | null) {
  inMemoryToken = token;
}

export function getSessionToken(): string | null {
  return inMemoryToken;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };

  if (inMemoryToken) {
    headers["Authorization"] = `Bearer ${inMemoryToken}`;
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = Array.isArray(body?.detail)
      ? body.detail.map((item: { msg?: string }) => item.msg).join(" ")
      : body?.detail || (typeof body?.message === "string" ? body.message : undefined);
    throw new Error(detail || "Something went wrong. Please try again.");
  }

  return response.status === 204 ? (undefined as T) : response.json();
}

async function ensureSession(): Promise<string> {
  if (inMemoryToken) return inMemoryToken;
  try {
    const profile = await request<UserProfile>("/api/auth/me");
    inMemoryToken = profile.token;
    return inMemoryToken;
  } catch {
    return "";
  }
}

export const api = {
  getAuthSession: async () => {
    const profile = await request<UserProfile>("/api/auth/me");
    inMemoryToken = profile.token;
    return profile;
  },
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

  // AI Provider Management
  getProviders: async () => {
    await ensureSession();
    return request<ProviderConnection[]>("/api/ai/providers");
  },
  connectProvider: async (provider: string, payload: { api_key?: string; base_url?: string; selected_model?: string }) => {
    await ensureSession();
    return request<ProviderConnection>(`/api/ai/providers/${provider}/connect`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  testConnection: async (provider: string, payload?: { api_key?: string; base_url?: string }) => {
    await ensureSession();
    return request<TestConnectionResponse>(`/api/ai/providers/${provider}/test`, {
      method: "POST",
      body: JSON.stringify(payload ?? {}),
    });
  },
  disconnectProvider: async (provider: string) => {
    await ensureSession();
    return request<void>(`/api/ai/providers/${provider}`, { method: "DELETE" });
  },
  updateProviderModel: async (provider: string, selected_model: string) => {
    await ensureSession();
    return request<ProviderConnection>(`/api/ai/providers/${provider}/model`, {
      method: "PATCH",
      body: JSON.stringify({ selected_model }),
    });
  },
  getAISettings: async () => {
    await ensureSession();
    return request<AISettings>("/api/ai/settings");
  },
  updateAISettings: async (payload: { default_provider?: string | null; default_model?: string | null }) => {
    await ensureSession();
    return request<AISettings>("/api/ai/settings", {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  },
  startOAuth: async (provider: string) => {
    await ensureSession();
    return request<{ authorization_url: string; state: string }>(`/api/ai/providers/${provider}/oauth/authorize`);
  },
  handleOAuthCallback: async (provider: string, code: string, state: string) => {
    await ensureSession();
    return request<ProviderConnection>(`/api/ai/providers/${provider}/oauth/callback`, {
      method: "POST",
      body: JSON.stringify({ code, state }),
    });
  },
  testGenerate: async (prompt: string, provider?: string, model?: string) => {
    await ensureSession();
    return request<TestGenerateResponse>("/api/ai/test-generate", {
      method: "POST",
      body: JSON.stringify({ prompt, provider, model }),
    });
  },
};
