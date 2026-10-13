"use client";

import {
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  Cpu,
  KeyRound,
  LayoutDashboard,
  Link as LinkIcon,
  LoaderCircle,
  Play,
  RotateCw,
  ShieldCheck,
  Sparkles,
  Star,
  Trash2,
  UsersRound,
  X,
} from "lucide-react";
import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  api,
  AISettings,
  ProviderConnection,
  TestConnectionResponse,
} from "@/lib/api";

const statusBadges: Record<
  ProviderConnection["status"],
  { label: string; className: string }
> = {
  connected: { label: "Connected", className: "status-won" },
  error: { label: "Connection Error", className: "status-lost" },
  expired: { label: "Token Expired", className: "status-replied" },
  disconnected: { label: "Not Connected", className: "status-new" },
};

export default function AIProvidersPage() {
  const [providers, setProviders] = useState<ProviderConnection[]>([]);
  const [aiSettings, setAiSettings] = useState<AISettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Connect drawer state
  const [connectingProvider, setConnectingProvider] =
    useState<ProviderConnection | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [baseUrlInput, setBaseUrlInput] = useState("");
  const [selectedModelInput, setSelectedModelInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");

  // Test states
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<
    Record<string, { success: boolean; message: string }>
  >({});

  // Disconnect confirmation
  const [disconnecting, setDisconnecting] =
    useState<ProviderConnection | null>(null);
  const [isDisconnecting, setIsDisconnecting] = useState(false);

  // Updating model state
  const [updatingModelFor, setUpdatingModelFor] = useState<string | null>(null);

  // Test prompt playground
  const [testPrompt, setTestPrompt] = useState(
    "Draft a concise 2-sentence value proposition for a modern B2B SaaS platform."
  );
  const [promptProvider, setPromptProvider] = useState("");
  const [promptModel, setPromptModel] = useState("");
  const [promptLoading, setPromptLoading] = useState(false);
  const [promptResult, setPromptResult] = useState<string | null>(null);
  const [promptError, setPromptError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [provList, settingsRes] = await Promise.all([
        api.getProviders(),
        api.getAISettings(),
      ]);
      setProviders(provList);
      setAiSettings(settingsRes);

      // Preselect provider for playground if available
      const connected = provList.find((p) => p.status === "connected");
      if (settingsRes.default_provider) {
        setPromptProvider(settingsRes.default_provider);
        setPromptModel(settingsRes.default_model || "");
      } else if (connected) {
        setPromptProvider(connected.provider);
        setPromptModel(connected.selected_model);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load AI providers from the LeadOps backend."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  function openConnectDrawer(p: ProviderConnection) {
    setConnectingProvider(p);
    setApiKeyInput("");
    setBaseUrlInput(p.base_url || (p.provider === "ollama" ? "http://localhost:11434" : ""));
    setSelectedModelInput(p.selected_model || "");
    setFormError("");
  }

  async function handleConnectSubmit(event: FormEvent) {
    event.preventDefault();
    if (!connectingProvider) return;
    setSaving(true);
    setFormError("");

    try {
      const payload: { api_key?: string; base_url?: string; selected_model?: string } = {};
      if (connectingProvider.provider === "ollama") {
        payload.base_url = baseUrlInput || "http://localhost:11434";
      } else {
        payload.api_key = apiKeyInput;
        if (baseUrlInput) payload.base_url = baseUrlInput;
      }
      if (selectedModelInput) payload.selected_model = selectedModelInput;

      await api.connectProvider(connectingProvider.provider, payload);
      setConnectingProvider(null);
      await loadData();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Failed to connect provider.");
    } finally {
      setSaving(false);
    }
  }

  async function handleTestConnection(p: ProviderConnection) {
    setTestingProvider(p.provider);
    try {
      const res: TestConnectionResponse = await api.testConnection(p.provider);
      setTestResults((prev) => ({
        ...prev,
        [p.provider]: { success: res.success, message: res.message },
      }));
      if (res.success) {
        await loadData();
      }
    } catch (err) {
      setTestResults((prev) => ({
        ...prev,
        [p.provider]: {
          success: false,
          message: err instanceof Error ? err.message : "Connection test failed.",
        },
      }));
    } finally {
      setTestingProvider(null);
    }
  }

  async function handleOAuthConnect(p: ProviderConnection) {
    setError("");
    try {
      const { authorization_url } = await api.startOAuth(p.provider);
      window.location.href = authorization_url;
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : `Failed to start OAuth flow for ${p.name}.`
      );
    }
  }

  async function handleSetDefault(p: ProviderConnection) {
    try {
      await api.updateAISettings({
        default_provider: p.provider,
        default_model: p.selected_model,
      });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update default provider.");
    }
  }

  async function handleModelChange(p: ProviderConnection, newModel: string) {
    setUpdatingModelFor(p.provider);
    try {
      await api.updateProviderModel(p.provider, newModel);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update model.");
    } finally {
      setUpdatingModelFor(null);
    }
  }

  async function handleDisconnectConfirm() {
    if (!disconnecting) return;
    setIsDisconnecting(true);
    try {
      await api.disconnectProvider(disconnecting.provider);
      setDisconnecting(null);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to disconnect provider.");
    } finally {
      setIsDisconnecting(false);
    }
  }

  async function handleRunTestPrompt() {
    if (!testPrompt.trim()) return;
    setPromptLoading(true);
    setPromptResult(null);
    setPromptError(null);

    try {
      const res = await api.testGenerate(
        testPrompt,
        promptProvider || undefined,
        promptModel || undefined
      );
      setPromptResult(res.response);
    } catch (err) {
      setPromptError(err instanceof Error ? err.message : "Test generation failed.");
    } finally {
      setPromptLoading(false);
    }
  }

  const connectedCount = providers.filter((p) => p.status === "connected").length;

  return (
    <main className="workspace">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">L</span>
          <span>leadops</span>
        </div>
        <nav aria-label="Main navigation">
          <Link className="nav-link" href="/">
            <LayoutDashboard size={18} />
            Overview
          </Link>
          <Link className="nav-link" href="/#leads">
            <UsersRound size={18} />
            Leads
          </Link>
          <Link className="nav-link active" href="/settings/ai-providers">
            <Cpu size={18} />
            AI Providers
            <span className="nav-count">{connectedCount} active</span>
          </Link>
        </nav>
        <div className="sidebar-foot">
          <div className="user-card">
            <div className="avatar">LO</div>
            <div>
              <strong>Local workspace</strong>
              <span>Lead manager</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <section className="content">
        <header className="topbar">
          <div>
            <p className="utility-label">Workspace Settings</p>
            <h1>AI Provider Connections</h1>
          </div>
          <button
            className="secondary-button"
            onClick={() => void loadData()}
            disabled={loading}
          >
            <RotateCw size={15} className={loading ? "spin" : ""} />
            Refresh
          </button>
        </header>

        {error && (
          <div className="api-error" role="alert">
            <strong>Notice:</strong> {error}{" "}
            <button onClick={() => void loadData()}>Try again</button>
          </div>
        )}

        {/* Overview Banner */}
        <section
          style={{
            background: "var(--panel)",
            border: "1px solid var(--line)",
            borderRadius: 12,
            padding: "20px 24px",
            marginBottom: 32,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 16,
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <ShieldCheck size={18} style={{ color: "var(--accent)" }} />
              <strong style={{ fontSize: 15, color: "var(--ink)" }}>
                User-Scoped Credentials &amp; Encryption at Rest
              </strong>
            </div>
            <p style={{ margin: 0, fontSize: 13, color: "var(--muted)" }}>
              Provider keys and tokens are encrypted with AES-256 Fernet on the server.
              Credentials are never returned to the browser or logged.
            </p>
          </div>
          <div style={{ display: "flex", gap: 20, alignItems: "center" }}>
            <div>
              <span style={{ fontSize: 11, color: "var(--muted)", textTransform: "uppercase", fontWeight: 700, letterSpacing: ".08em", display: "block" }}>
                Active Default
              </span>
              <strong style={{ fontSize: 14, color: "var(--ink)" }}>
                {aiSettings?.default_provider ? (
                  providers.find((p) => p.provider === aiSettings.default_provider)?.name ?? aiSettings.default_provider
                ) : (
                  <span style={{ color: "var(--muted)", fontWeight: 500 }}>None selected</span>
                )}
              </strong>
            </div>
            {aiSettings?.default_model && (
              <div>
                <span style={{ fontSize: 11, color: "var(--muted)", textTransform: "uppercase", fontWeight: 700, letterSpacing: ".08em", display: "block" }}>
                  Default Model
                </span>
                <span style={{ fontSize: 13, color: "var(--ink)", fontFamily: "var(--font-mono)" }}>
                  {aiSettings.default_model}
                </span>
              </div>
            )}
          </div>
        </section>

        {/* Provider Cards List */}
        <section style={{ display: "grid", gap: 20, marginBottom: 40 }}>
          {loading ? (
            <div className="state-panel">
              <LoaderCircle className="spin" size={24} />
              Loading connected AI providers…
            </div>
          ) : (
            providers.map((p) => {
              const badge = statusBadges[p.status];
              const testResult = testResults[p.provider];
              const isDefault = p.is_default;

              return (
                <article
                  key={p.provider}
                  style={{
                    background: "var(--panel)",
                    border: isDefault ? "2px solid #80c7b5" : "1px solid var(--line)",
                    borderRadius: 12,
                    padding: "24px",
                    boxShadow: "0 2px 8px rgb(28 51 65 / .03)",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "flex-start",
                      flexWrap: "wrap",
                      gap: 12,
                      marginBottom: 16,
                    }}
                  >
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <h2 style={{ margin: 0, fontSize: 18, color: "var(--ink)", fontWeight: 700 }}>
                          {p.name}
                        </h2>
                        <span className={`status-badge ${badge.className}`}>
                          {badge.label}
                        </span>
                        {isDefault && (
                          <span
                            style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: 4,
                              fontSize: 11,
                              fontWeight: 700,
                              color: "var(--accent)",
                              background: "#e4f2ee",
                              padding: "3px 8px",
                              borderRadius: 99,
                            }}
                          >
                            <Star size={12} fill="var(--accent)" />
                            Default Provider
                          </span>
                        )}
                      </div>
                      <p style={{ margin: "6px 0 0", fontSize: 12, color: "var(--muted)" }}>
                        {p.connection_method === "oauth"
                          ? "Connected via OAuth token"
                          : p.connection_method === "local"
                          ? `Local instance at ${p.base_url || "http://localhost:11434"}`
                          : p.key_preview
                          ? `Masked Key: ${p.key_preview}`
                          : "No active connection"}
                      </p>
                    </div>

                    <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                      {p.status === "connected" && !isDefault && (
                        <button
                          className="secondary-button"
                          onClick={() => void handleSetDefault(p)}
                          title="Set as default provider for AI operations"
                        >
                          <Star size={14} />
                          Set default
                        </button>
                      )}

                      {p.status === "connected" && (
                        <button
                          className="secondary-button"
                          disabled={testingProvider === p.provider}
                          onClick={() => void handleTestConnection(p)}
                        >
                          {testingProvider === p.provider ? (
                            <LoaderCircle size={14} className="spin" />
                          ) : (
                            <Play size={14} />
                          )}
                          Test connection
                        </button>
                      )}

                      {p.status === "connected" ? (
                        <>
                          <button
                            className="secondary-button"
                            onClick={() => openConnectDrawer(p)}
                          >
                            <KeyRound size={14} />
                            Edit
                          </button>
                          <button
                            className="danger-button"
                            onClick={() => setDisconnecting(p)}
                          >
                            <Trash2 size={14} />
                            Disconnect
                          </button>
                        </>
                      ) : (
                        <div style={{ display: "flex", gap: 8 }}>
                          {p.supports_oauth && p.is_oauth_configured && (
                            <button
                              className="primary-button"
                              onClick={() => void handleOAuthConnect(p)}
                            >
                              <LinkIcon size={14} />
                              Connect with OAuth
                            </button>
                          )}
                          <button
                            className={p.supports_oauth && p.is_oauth_configured ? "secondary-button" : "primary-button"}
                            onClick={() => openConnectDrawer(p)}
                          >
                            <KeyRound size={14} />
                            {p.provider === "ollama" ? "Connect Local" : "Connect with API Key"}
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Test feedback */}
                  {testResult && (
                    <div
                      style={{
                        padding: "9px 12px",
                        borderRadius: 8,
                        fontSize: 12,
                        marginBottom: 16,
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                        background: testResult.success ? "#e9f7ee" : "#fff2f1",
                        color: testResult.success ? "#1e6c45" : "#87413e",
                        border: `1px solid ${testResult.success ? "#c2ebd0" : "#f5c6c4"}`,
                      }}
                    >
                      {testResult.success ? <CheckCircle2 size={15} /> : <AlertCircle size={15} />}
                      <span>{testResult.message}</span>
                    </div>
                  )}

                  {/* Connected settings: Model Selection */}
                  {p.status === "connected" && (
                    <div
                      style={{
                        borderTop: "1px solid var(--line)",
                        paddingTop: 16,
                        marginTop: 12,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        flexWrap: "wrap",
                        gap: 12,
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                        <span style={{ fontSize: 12, fontWeight: 700, color: "var(--ink)" }}>
                          Selected Model:
                        </span>
                        <label className="select-field" style={{ minWidth: 260 }}>
                          <select
                            value={p.selected_model}
                            disabled={updatingModelFor === p.provider}
                            onChange={(e) => void handleModelChange(p, e.target.value)}
                          >
                            {p.available_models.map((m) => (
                              <option key={m} value={m}>
                                {m}
                              </option>
                            ))}
                          </select>
                          <ChevronDown size={14} />
                        </label>
                        {updatingModelFor === p.provider && (
                          <LoaderCircle size={14} className="spin" style={{ color: "var(--muted)" }} />
                        )}
                      </div>

                      <span style={{ fontSize: 11, color: "var(--muted)" }}>
                        {p.available_models.length} model(s) available
                      </span>
                    </div>
                  )}

                  {/* Informative Limitation Notes */}
                  {p.status === "disconnected" && (
                    <div
                      style={{
                        borderTop: "1px solid #edf1f0",
                        paddingTop: 12,
                        marginTop: 10,
                        fontSize: 12,
                        color: "var(--muted)",
                      }}
                    >
                      {p.oauth_limitation ? (
                        <span>ℹ️ {p.oauth_limitation}</span>
                      ) : p.supports_oauth && p.is_oauth_configured ? (
                        <span>
                          Supports authorization via both official OAuth PKCE flow and direct API keys.
                        </span>
                      ) : null}
                    </div>
                  )}
                </article>
              );
            })
          )}
        </section>

        {/* Test Prompt Generation Playground */}
        <section
          style={{
            background: "var(--panel)",
            border: "1px solid var(--line)",
            borderRadius: 12,
            padding: "24px",
            marginBottom: 40,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <Sparkles size={18} style={{ color: "var(--accent)" }} />
            <h2 style={{ margin: 0, fontSize: 17, color: "var(--ink)", fontWeight: 700 }}>
              Live Generation Verification
            </h2>
          </div>
          <p style={{ margin: "0 0 18px", fontSize: 13, color: "var(--muted)" }}>
            Send a minimal prompt to verify text generation end-to-end through your connected provider.
          </p>

          <div style={{ display: "grid", gap: 14 }}>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              <label className="select-field" style={{ flex: 1, minWidth: 200 }}>
                <select
                  value={promptProvider}
                  onChange={(e) => {
                    setPromptProvider(e.target.value);
                    const selected = providers.find((p) => p.provider === e.target.value);
                    if (selected) setPromptModel(selected.selected_model);
                  }}
                >
                  <option value="">Use Default Provider</option>
                  {providers
                    .filter((p) => p.status === "connected")
                    .map((p) => (
                      <option key={p.provider} value={p.provider}>
                        {p.name} {p.is_default ? "(Default)" : ""}
                      </option>
                    ))}
                </select>
                <ChevronDown size={14} />
              </label>

              {promptProvider && (
                <label className="select-field" style={{ flex: 1, minWidth: 200 }}>
                  <select
                    value={promptModel}
                    onChange={(e) => setPromptModel(e.target.value)}
                  >
                    {(providers.find((p) => p.provider === promptProvider)?.available_models || []).map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </select>
                  <ChevronDown size={14} />
                </label>
              )}
            </div>

            <textarea
              rows={3}
              placeholder="Enter a test prompt…"
              value={testPrompt}
              onChange={(e) => setTestPrompt(e.target.value)}
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: 8,
                border: "1px solid #d4dcda",
                fontSize: 13,
                resize: "vertical",
              }}
            />

            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button
                className="primary-button"
                disabled={promptLoading || connectedCount === 0 || !testPrompt.trim()}
                onClick={() => void handleRunTestPrompt()}
              >
                {promptLoading ? (
                  <LoaderCircle size={15} className="spin" />
                ) : (
                  <Play size={15} />
                )}
                Run Test Generation
              </button>
            </div>

            {promptError && (
              <div
                style={{
                  padding: "12px",
                  borderRadius: 8,
                  fontSize: 13,
                  background: "#fff2f1",
                  color: "#87413e",
                  border: "1px solid #f5c6c4",
                }}
              >
                <strong>Error:</strong> {promptError}
              </div>
            )}

            {promptResult && (
              <div
                style={{
                  marginTop: 6,
                  padding: "16px",
                  borderRadius: 8,
                  background: "#f9faf9",
                  border: "1px solid var(--line)",
                }}
              >
                <span style={{ fontSize: 11, fontWeight: 700, color: "var(--muted)", textTransform: "uppercase" }}>
                  Generated Response:
                </span>
                <p style={{ margin: "8px 0 0", fontSize: 13, lineHeight: 1.6, whiteSpace: "pre-wrap", color: "var(--ink)" }}>
                  {promptResult}
                </p>
              </div>
            )}
          </div>
        </section>
      </section>

      {/* Connect Drawer */}
      {connectingProvider && (
        <div
          className="drawer-backdrop"
          role="presentation"
          onMouseDown={() => setConnectingProvider(null)}
        >
          <aside
            className="drawer"
            role="dialog"
            aria-modal="true"
            aria-labelledby="connect-drawer-title"
            onMouseDown={(e) => e.stopPropagation()}
          >
            <div className="drawer-heading">
              <div>
                <p className="utility-label">Connection Credentials</p>
                <h2 id="connect-drawer-title">Connect {connectingProvider.name}</h2>
              </div>
              <button
                className="icon-button"
                type="button"
                aria-label="Close"
                onClick={() => setConnectingProvider(null)}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleConnectSubmit} className="lead-form">
              {connectingProvider.provider !== "ollama" ? (
                <>
                  <label>
                    API Key
                    <input
                      required
                      type="password"
                      placeholder="sk-..."
                      value={apiKeyInput}
                      onChange={(e) => setApiKeyInput(e.target.value)}
                    />
                  </label>
                  <label>
                    Custom Base URL (Optional)
                    <input
                      type="url"
                      placeholder={
                        connectingProvider.provider === "openai"
                          ? "https://api.openai.com/v1"
                          : "Leave blank for provider default"
                      }
                      value={baseUrlInput}
                      onChange={(e) => setBaseUrlInput(e.target.value)}
                    />
                  </label>
                </>
              ) : (
                <>
                  <label>
                    Ollama Server URL
                    <input
                      required
                      type="url"
                      placeholder="http://localhost:11434"
                      value={baseUrlInput}
                      onChange={(e) => setBaseUrlInput(e.target.value)}
                    />
                  </label>
                </>
              )}

              <label>
                Preferred Default Model (Optional)
                <input
                  placeholder={connectingProvider.selected_model}
                  value={selectedModelInput}
                  onChange={(e) => setSelectedModelInput(e.target.value)}
                />
              </label>

              {formError && (
                <p className="form-error" role="alert">
                  {formError}
                </p>
              )}

              <div className="form-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setConnectingProvider(null)}
                >
                  Cancel
                </button>
                <button className="primary-button" disabled={saving}>
                  {saving && <LoaderCircle className="spin" size={16} />}
                  Save &amp; Connect
                </button>
              </div>
            </form>
          </aside>
        </div>
      )}

      {/* Disconnect Confirmation Modal */}
      {disconnecting && (
        <div className="confirm-layer" role="presentation">
          <div className="confirm-card" role="alertdialog" aria-modal="true">
            <h2>Disconnect {disconnecting.name}?</h2>
            <p>
              This removes your stored credentials and connection settings for {disconnecting.name}.
              If connected via OAuth, stored tokens will be revoked upstream where supported.
            </p>
            <div>
              <button
                className="secondary-button"
                disabled={isDisconnecting}
                onClick={() => setDisconnecting(null)}
              >
                Cancel
              </button>
              <button
                className="danger-button"
                disabled={isDisconnecting}
                onClick={() => void handleDisconnectConfirm()}
              >
                {isDisconnecting ? "Disconnecting…" : "Disconnect"}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
