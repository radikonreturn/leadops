"use client";

import dynamic from "next/dynamic";

const LeadWorkspace = dynamic(() => import("./lead-workspace"), {
  ssr: false,
  loading: () => <main className="workspace"><div className="state-panel" aria-busy="true">Loading LeadOps…</div></main>,
});

export default function Home() {
  return <LeadWorkspace />;
}
