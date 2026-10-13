"use client";

import dynamic from "next/dynamic";

const LeadWorkspace = dynamic(() => import("./lead-workspace"), {
  ssr: false,
  loading: () => <main className="workspace" aria-busy="true" />,
});

export default function Home() {
  return <LeadWorkspace />;
}
