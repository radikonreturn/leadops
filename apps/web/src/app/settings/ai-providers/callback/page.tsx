"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { LoaderCircle, AlertCircle, CheckCircle } from "lucide-react";
import { api } from "@/lib/api";

function OAuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("Completing OAuth authorization…");

  useEffect(() => {
    async function processCallback() {
      const code = searchParams.get("code");
      const state = searchParams.get("state");
      const errorParam = searchParams.get("error");
      const errorDescription = searchParams.get("error_description");

      if (errorParam) {
        setStatus("error");
        setMessage(errorDescription || `Provider returned an error: ${errorParam}`);
        return;
      }

      if (!code || !state) {
        setStatus("error");
        setMessage("Missing authorization code or state in OAuth callback.");
        return;
      }

      try {
        try {
          await api.handleOAuthCallback("openrouter", code, state);
        } catch {
          await api.handleOAuthCallback("gemini", code, state);
        }
        setStatus("success");
        setMessage("Connected successfully! Redirecting to AI Providers…");
        setTimeout(() => {
          router.push("/settings/ai-providers");
        }, 1200);
      } catch (err) {
        setStatus("error");
        setMessage(err instanceof Error ? err.message : "Failed to complete OAuth exchange.");
      }
    }

    processCallback();
  }, [router, searchParams]);

  return (
    <div className="confirm-card" style={{ maxWidth: 460, textAlign: "center" }}>
      {status === "loading" && (
        <>
          <LoaderCircle className="spin" size={32} style={{ margin: "0 auto 16px", color: "var(--accent)" }} />
          <h2>Connecting AI Provider</h2>
          <p>{message}</p>
        </>
      )}
      {status === "success" && (
        <>
          <CheckCircle size={32} style={{ margin: "0 auto 16px", color: "#1e6c45" }} />
          <h2>Authorization Complete</h2>
          <p>{message}</p>
        </>
      )}
      {status === "error" && (
        <>
          <AlertCircle size={32} style={{ margin: "0 auto 16px", color: "#b63d3c" }} />
          <h2>Connection Error</h2>
          <p style={{ color: "#87413e" }}>{message}</p>
          <div style={{ justifyContent: "center", marginTop: 20 }}>
            <button
              className="primary-button"
              onClick={() => router.push("/settings/ai-providers")}
            >
              Back to AI Providers
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default function OAuthCallbackPage() {
  return (
    <main className="workspace" style={{ alignItems: "center", justifyContent: "center" }}>
      <Suspense
        fallback={
          <div className="confirm-card" style={{ maxWidth: 460, textAlign: "center" }}>
            <LoaderCircle className="spin" size={32} style={{ margin: "0 auto 16px", color: "var(--accent)" }} />
            <h2>Connecting AI Provider</h2>
            <p>Loading callback parameters…</p>
          </div>
        }
      >
        <OAuthCallbackContent />
      </Suspense>
    </main>
  );
}

