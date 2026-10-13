import pytest
from fastapi import HTTPException

from app.api.leads import (
    create_lead,
    delete_lead,
    get_dashboard_summary,
    get_lead,
    list_leads,
    update_lead,
    update_lead_status,
)
from app.main import health_check
from app.schemas.lead import LeadCreate, LeadStatusUpdate, LeadUpdate


def lead_payload(**overrides):
    payload = {
        "company_name": "Northstar Systems",
        "website": "https://northstar.example",
        "contact_name": "Avery Patel",
        "email": "avery@northstar.example",
        "industry": "Software",
        "source": "Referral",
        "status": "New",
        "notes": "Asked for a short product overview.",
    }
    payload.update(overrides)
    return payload


def test_health_check():
    assert health_check() == {"status": "ok"}


def test_lead_crud_search_filter_and_dashboard_metrics(db):
    lead = create_lead(LeadCreate(**lead_payload()), db)

    assert lead.company_name == "Northstar Systems"
    assert lead.status == "New"

    updated = update_lead(
        lead.id,
        LeadUpdate(contact_name="Avery Chen", notes="Discovery scheduled."),
        db,
    )
    assert updated.contact_name == "Avery Chen"

    status_changed = update_lead_status(lead.id, LeadStatusUpdate(status="Qualified"), db)
    assert status_changed.status == "Qualified"

    response = list_leads(search="avery", status_filter="Qualified", industry="Software", db=db)
    assert [item.id for item in response.items] == [lead.id]
    assert response.industries == ["Software"]

    summary = get_dashboard_summary(db)
    assert summary.total_leads == 1
    assert summary.new_leads == 0
    assert summary.qualified_prospects == 1
    assert summary.recent_leads[0].id == lead.id

    deleted = delete_lead(lead.id, db)
    assert deleted.status_code == 204
    with pytest.raises(HTTPException) as exception:
        get_lead(lead.id, db)
    assert exception.value.status_code == 404


def test_invalid_status_is_rejected():
    with pytest.raises(ValueError):
        LeadCreate(**lead_payload(status="Researching"))
