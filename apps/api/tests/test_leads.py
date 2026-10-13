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
from app.models.company import Company
from app.models.lead import Lead
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


@pytest.mark.parametrize("field", ["company_name", "contact_name", "industry", "source"])
def test_partial_update_rejects_blank_required_text(field):
    with pytest.raises(ValueError):
        LeadUpdate(**{field: "   "})


def test_deleting_a_lead_preserves_other_leads_for_the_same_company(db):
    created = create_lead(LeadCreate(**lead_payload()), db)
    original_lead = db.get(Lead, created.id)
    shared_lead = Lead(company=original_lead.company, status="Contacted", source="Manual")
    db.add(shared_lead)
    db.commit()

    delete_lead(created.id, db)

    assert db.get(Lead, shared_lead.id) is not None
    assert db.query(Company).count() == 1

    delete_lead(shared_lead.id, db)
    assert db.query(Lead).count() == 0
    assert db.query(Company).count() == 0


def test_dashboard_and_leads_endpoints_via_http_client(db):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.database import get_db

    app.dependency_overrides[get_db] = lambda: db
    try:
        client = TestClient(app)
        summary_res = client.get("/api/dashboard/summary")
        assert summary_res.status_code == 200
        assert summary_res.json() == {
            "total_leads": 0,
            "new_leads": 0,
            "qualified_prospects": 0,
            "follow_ups_pending": 0,
            "recent_leads": [],
        }

        leads_res = client.get("/api/leads")
        assert leads_res.status_code == 200
        assert leads_res.json() == {"items": [], "industries": []}
    finally:
        app.dependency_overrides.clear()

