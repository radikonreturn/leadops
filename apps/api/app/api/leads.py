from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.company import Company
from app.models.lead import Lead
from app.schemas.lead import (
    DashboardSummary,
    LeadCreate,
    LeadListResponse,
    LeadResponse,
    LeadStatus,
    LeadStatusUpdate,
    LeadUpdate,
)

router = APIRouter(prefix="/api/leads", tags=["leads"])
dashboard_router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def get_lead_or_404(db: Session, lead_id: int) -> Lead:
    lead = (
        db.query(Lead)
        .options(joinedload(Lead.company))
        .filter(Lead.id == lead_id)
        .first()
    )
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")
    return lead


def serialize_lead(lead: Lead) -> LeadResponse:
    return LeadResponse(
        id=lead.id,
        company_name=lead.company.name,
        website=lead.company.website,
        contact_name=lead.company.contact_name,
        email=lead.company.email,
        industry=lead.company.industry,
        source=lead.source,
        status=lead.status,
        notes=lead.notes,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )


@router.get("", response_model=LeadListResponse)
def list_leads(
    search: Optional[str] = Query(default=None, max_length=120),
    status_filter: Optional[LeadStatus] = Query(default=None, alias="status"),
    industry: Optional[str] = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
) -> LeadListResponse:
    query = db.query(Lead).join(Company).options(joinedload(Lead.company))
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Company.name.ilike(term),
                Company.contact_name.ilike(term),
                Company.email.ilike(term),
                Company.industry.ilike(term),
            )
        )
    if status_filter:
        query = query.filter(Lead.status == status_filter)
    if industry:
        query = query.filter(Company.industry == industry)

    leads = query.order_by(Lead.updated_at.desc()).all()
    industries = [
        row[0]
        for row in db.query(Company.industry)
        .filter(Company.industry.isnot(None), Company.industry != "")
        .distinct()
        .order_by(Company.industry)
        .all()
    ]
    return LeadListResponse(items=[serialize_lead(lead) for lead in leads], industries=industries)


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)) -> LeadResponse:
    company = Company(
        name=payload.company_name,
        website=str(payload.website),
        contact_name=payload.contact_name,
        email=str(payload.email) if payload.email else None,
        industry=payload.industry,
    )
    lead = Lead(company=company, source=payload.source, status=payload.status, notes=payload.notes)
    db.add(lead)
    db.commit()
    db.refresh(lead)
    db.refresh(company)
    return serialize_lead(lead)


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)) -> LeadResponse:
    return serialize_lead(get_lead_or_404(db, lead_id))


@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead(lead_id: int, payload: LeadUpdate, db: Session = Depends(get_db)) -> LeadResponse:
    lead = get_lead_or_404(db, lead_id)
    updates = payload.model_dump(exclude_unset=True)
    company_fields = {"company_name": "name", "website": "website", "contact_name": "contact_name", "email": "email", "industry": "industry"}
    for field, value in updates.items():
        if field in company_fields:
            setattr(lead.company, company_fields[field], str(value) if value is not None else None)
        else:
            setattr(lead, field, value)
    lead.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(lead)
    return serialize_lead(lead)


@router.patch("/{lead_id}/status", response_model=LeadResponse)
def update_lead_status(lead_id: int, payload: LeadStatusUpdate, db: Session = Depends(get_db)) -> LeadResponse:
    lead = get_lead_or_404(db, lead_id)
    lead.status = payload.status
    lead.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(lead)
    return serialize_lead(lead)


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: int, db: Session = Depends(get_db)) -> Response:
    lead = get_lead_or_404(db, lead_id)
    company = lead.company
    db.delete(lead)
    db.flush()
    if db.query(Lead.id).filter(Lead.company_id == company.id).first() is None:
        db.delete(company)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@dashboard_router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    total = db.query(func.count(Lead.id)).scalar() or 0
    by_status = dict(db.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all())
    recent = (
        db.query(Lead)
        .options(joinedload(Lead.company))
        .order_by(Lead.created_at.desc())
        .limit(5)
        .all()
    )
    return DashboardSummary(
        total_leads=total,
        new_leads=by_status.get("New", 0),
        qualified_prospects=by_status.get("Qualified", 0),
        follow_ups_pending=by_status.get("Contacted", 0) + by_status.get("Replied", 0),
        recent_leads=[serialize_lead(lead) for lead in recent],
    )
