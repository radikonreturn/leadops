"use client";

import {
  Building2,
  ChevronDown,
  Clock3,
  Cpu,
  Eye,
  LayoutDashboard,
  LoaderCircle,
  Pencil,
  Plus,
  Search,
  Target,
  Trash2,
  UsersRound,
  X,
} from "lucide-react";
import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { api, DashboardSummary, Lead, LeadPayload, LeadStatus, leadStatuses } from "@/lib/api";

const blankLead: LeadPayload = {
  company_name: "",
  website: "",
  contact_name: "",
  email: "",
  industry: "",
  source: "Manual",
  status: "New",
  notes: "",
};

const statusClass: Record<LeadStatus, string> = {
  New: "status-new",
  Qualified: "status-qualified",
  Contacted: "status-contacted",
  Replied: "status-replied",
  Won: "status-won",
  Lost: "status-lost",
};

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", year: "numeric" }).format(new Date(value));
}

function LeadForm({ lead, onClose, onSaved }: { lead: Lead | null; onClose: () => void; onSaved: () => Promise<void> }) {
  const [form, setForm] = useState<LeadPayload>(lead ? { ...lead } : blankLead);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function changeField(field: keyof LeadPayload, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      if (lead) await api.updateLead(lead.id, form);
      else await api.createLead(form);
      await onSaved();
      onClose();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save the lead.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="drawer-backdrop" role="presentation" onMouseDown={onClose}>
      <aside className="drawer" role="dialog" aria-modal="true" aria-labelledby="lead-form-title" onMouseDown={(event) => event.stopPropagation()}>
        <div className="drawer-heading">
          <div>
            <p className="utility-label">{lead ? "Edit record" : "New record"}</p>
            <h2 id="lead-form-title">{lead ? lead.company_name : "Add a lead"}</h2>
          </div>
          <button className="icon-button" type="button" aria-label="Close form" onClick={onClose}><X size={18} /></button>
        </div>
        <form onSubmit={submit} className="lead-form">
          <div className="form-section"><span>Company</span></div>
          <label>Company name<input required value={form.company_name} onChange={(event) => changeField("company_name", event.target.value)} /></label>
          <label>Website URL<input required type="url" placeholder="https://company.com" value={form.website} onChange={(event) => changeField("website", event.target.value)} /></label>
          <label>Industry<input required value={form.industry} onChange={(event) => changeField("industry", event.target.value)} /></label>
          <div className="form-section"><span>Primary contact</span></div>
          <label>Contact name<input required value={form.contact_name} onChange={(event) => changeField("contact_name", event.target.value)} /></label>
          <label>Email address<input type="email" value={form.email ?? ""} onChange={(event) => changeField("email", event.target.value)} /></label>
          <div className="form-grid">
            <label>Lead source<input required value={form.source} onChange={(event) => changeField("source", event.target.value)} /></label>
            <label>Status<select value={form.status} onChange={(event) => changeField("status", event.target.value)}>{leadStatuses.map((status) => <option key={status}>{status}</option>)}</select></label>
          </div>
          <label>Notes<textarea rows={5} placeholder="Context, next step, or qualification notes" value={form.notes ?? ""} onChange={(event) => changeField("notes", event.target.value)} /></label>
          {error && <p className="form-error" role="alert">{error}</p>}
          <div className="form-actions"><button type="button" className="secondary-button" onClick={onClose}>Cancel</button><button className="primary-button" disabled={saving}>{saving && <LoaderCircle className="spin" size={16} />}{lead ? "Save changes" : "Create lead"}</button></div>
        </form>
      </aside>
    </div>
  );
}

export default function Home() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [industries, setIndustries] = useState<string[]>([]);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [industryFilter, setIndustryFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editingLead, setEditingLead] = useState<Lead | null | undefined>(undefined);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [deleting, setDeleting] = useState<Lead | null>(null);
  const [updatingLeadId, setUpdatingLeadId] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [leadResponse, dashboardResponse] = await Promise.all([api.getLeads(search, statusFilter, industryFilter), api.getSummary()]);
      setLeads(leadResponse.items);
      setIndustries(leadResponse.industries);
      setSummary(dashboardResponse);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to reach the LeadOps API.");
    } finally {
      setLoading(false);
    }
  }, [industryFilter, search, statusFilter]);

  useEffect(() => {
    const timeout = window.setTimeout(() => void loadData(), 200);
    return () => window.clearTimeout(timeout);
  }, [loadData]);

  const visibleLead = useMemo(() => selectedLead && leads.find((lead) => lead.id === selectedLead.id), [leads, selectedLead]);

  async function changeStatus(lead: Lead, status: LeadStatus) {
    setUpdatingLeadId(lead.id);
    try {
      await api.updateStatus(lead.id, status);
      await loadData();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not update the lead status.");
    } finally {
      setUpdatingLeadId(null);
    }
  }

  async function deleteLead() {
    if (!deleting) return;
    setIsDeleting(true);
    try {
      await api.deleteLead(deleting.id);
      setDeleting(null);
      setSelectedLead(null);
      await loadData();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not delete the lead.");
    } finally {
      setIsDeleting(false);
    }
  }

  const metrics = [
    ["Total leads", summary?.total_leads ?? 0, UsersRound, "Across the full pipeline"],
    ["New leads", summary?.new_leads ?? 0, Plus, "Awaiting first review"],
    ["Qualified", summary?.qualified_prospects ?? 0, Target, "Ready for outreach"],
    ["Follow-ups", summary?.follow_ups_pending ?? 0, Clock3, "Contacted or replied"],
  ] as const;

  return (
    <main className="workspace">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">L</span><span>leadops</span></div>
        <nav aria-label="Main navigation">
          <a className="nav-link active" href="#dashboard"><LayoutDashboard size={18} />Overview</a>
          <a className="nav-link" href="#leads"><UsersRound size={18} />Leads <span className="nav-count">{summary?.total_leads ?? 0}</span></a>
          <Link className="nav-link" href="/settings/ai-providers"><Cpu size={18} />AI Providers</Link>
        </nav>
        <div className="sidebar-foot"><div className="user-card"><div className="avatar">LO</div><div><strong>Local workspace</strong><span>Lead manager</span></div></div></div>
      </aside>
      <section className="content">
        <header className="topbar"><div><p className="utility-label">Sales workspace</p><h1>Pipeline overview</h1></div><button className="primary-button" onClick={() => setEditingLead(null)}><Plus size={17} />Add lead</button></header>
        <section id="dashboard" className="metrics" aria-label="Lead metrics">{metrics.map(([label, amount, Icon, copy]) => <article key={label} className="metric"><div className="metric-icon"><Icon size={18} /></div><p>{label}</p><strong>{amount}</strong><span>{copy}</span></article>)}</section>
        <section id="leads" className="lead-section"><div className="section-heading"><div><h2>Leads</h2><p>Capture, qualify, and keep your next conversation moving.</p></div><span className="record-count">{leads.length} shown</span></div>
          <div className="filters"><label className="search-field"><Search size={17} /><input aria-label="Search leads" placeholder="Search company, contact, email…" value={search} onChange={(event) => setSearch(event.target.value)} /></label><label className="select-field"><select aria-label="Filter by status" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}><option value="">All statuses</option>{leadStatuses.map((status) => <option key={status}>{status}</option>)}</select><ChevronDown size={15} /></label><label className="select-field"><select aria-label="Filter by industry" value={industryFilter} onChange={(event) => setIndustryFilter(event.target.value)}><option value="">All industries</option>{industries.map((industry) => <option key={industry}>{industry}</option>)}</select><ChevronDown size={15} /></label></div>
          {error && <div className="api-error" role="alert"><strong>Connection issue.</strong> {error} <button onClick={() => void loadData()}>Try again</button></div>}
          <div className="table-wrap">{loading ? <div className="state-panel"><LoaderCircle className="spin" size={22} />Loading your lead workspace…</div> : leads.length === 0 ? <div className="state-panel"><Building2 size={24} /><strong>No leads found</strong><span>{search || statusFilter || industryFilter ? "Try clearing a filter or search term." : "Add your first prospect to start building the pipeline."}</span>{!search && !statusFilter && !industryFilter && <button className="secondary-button" onClick={() => setEditingLead(null)}>Add first lead</button>}</div> : <table><thead><tr><th>Company</th><th>Contact</th><th>Industry</th><th>Source</th><th>Status</th><th>Updated</th><th><span className="sr-only">Actions</span></th></tr></thead><tbody>{leads.map((lead) => <tr key={lead.id} onClick={() => setSelectedLead(lead)}><td><div className="company-cell"><span className="company-initial">{lead.company_name.slice(0, 1).toUpperCase()}</span><div><strong>{lead.company_name}</strong><a onClick={(event) => event.stopPropagation()} href={lead.website} target="_blank" rel="noreferrer">{lead.website.replace(/^https?:\/\//, "")}</a></div></div></td><td><strong>{lead.contact_name}</strong><span>{lead.email || "No email"}</span></td><td>{lead.industry}</td><td>{lead.source}</td><td onClick={(event) => event.stopPropagation()}><select aria-label={`Change ${lead.company_name} status`} className={`status-select ${statusClass[lead.status]}`} value={lead.status} disabled={updatingLeadId === lead.id} aria-busy={updatingLeadId === lead.id} onChange={(event) => void changeStatus(lead, event.target.value as LeadStatus)}>{leadStatuses.map((status) => <option key={status}>{status}</option>)}</select></td><td><time dateTime={lead.updated_at}>{formatDate(lead.updated_at)}</time></td><td onClick={(event) => event.stopPropagation()}><div className="table-actions"><button className="icon-button" aria-label={`View ${lead.company_name}`} onClick={() => setSelectedLead(lead)}><Eye size={16} /></button><button className="icon-button" aria-label={`Edit ${lead.company_name}`} onClick={() => setEditingLead(lead)}><Pencil size={16} /></button></div></td></tr>)}</tbody></table>}</div>
        </section>
      </section>
      {editingLead !== undefined && <LeadForm lead={editingLead} onClose={() => setEditingLead(undefined)} onSaved={loadData} />}
      {visibleLead && <div className="drawer-backdrop detail-backdrop" role="presentation" onMouseDown={() => setSelectedLead(null)}><aside className="drawer detail-drawer" role="dialog" aria-modal="true" aria-labelledby="lead-detail-title" onMouseDown={(event) => event.stopPropagation()}><div className="drawer-heading"><div><p className="utility-label">Lead record</p><h2 id="lead-detail-title">{visibleLead.company_name}</h2></div><button className="icon-button" aria-label="Close lead details" onClick={() => setSelectedLead(null)}><X size={18} /></button></div><div className="detail-content"><span className={`status-badge ${statusClass[visibleLead.status]}`}>{visibleLead.status}</span><dl><div><dt>Website</dt><dd><a href={visibleLead.website} target="_blank" rel="noreferrer">{visibleLead.website}</a></dd></div><div><dt>Contact</dt><dd>{visibleLead.contact_name}</dd></div><div><dt>Email</dt><dd>{visibleLead.email || "Not recorded"}</dd></div><div><dt>Industry</dt><dd>{visibleLead.industry}</dd></div><div><dt>Source</dt><dd>{visibleLead.source}</dd></div><div><dt>Created</dt><dd>{formatDate(visibleLead.created_at)}</dd></div><div><dt>Last updated</dt><dd>{formatDate(visibleLead.updated_at)}</dd></div></dl><div className="notes"><span>Notes</span><p>{visibleLead.notes || "No notes recorded yet."}</p></div><div className="detail-actions"><button className="secondary-button" onClick={() => { setSelectedLead(null); setEditingLead(visibleLead); }}><Pencil size={16} />Edit lead</button><button className="danger-button" onClick={() => setDeleting(visibleLead)}><Trash2 size={16} />Delete</button></div></div></aside></div>}
      {deleting && <div className="confirm-layer" role="presentation"><div className="confirm-card" role="alertdialog" aria-modal="true" aria-labelledby="delete-title"><h2 id="delete-title">Delete {deleting.company_name}?</h2><p>This permanently removes this lead. The company remains when it has other lead records.</p><div><button className="secondary-button" disabled={isDeleting} onClick={() => setDeleting(null)}>Cancel</button><button className="danger-button" disabled={isDeleting} onClick={() => void deleteLead()}>{isDeleting ? "Deleting…" : "Delete lead"}</button></div></div></div>}
    </main>
  );
}
