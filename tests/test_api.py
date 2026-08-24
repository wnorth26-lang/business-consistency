from fastapi.testclient import TestClient

from business_consistency.api import app


client = TestClient(app)


def test_subscription_access_detects_violation():
    response = client.post("/v1/check/subscription-access", json={
        "customer_id": "cus_123",
        "billing_status": "active",
        "access_plan": "free",
    })
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "violation"
    assert body["verified"] is False
    assert body["violations"][0]["expected"] == "pro"


def test_generic_verifier_passes_consistent_state():
    response = client.post("/v1/verify", json={
        "subject_id": "deal_123",
        "invariant": {
            "name": "closed_won_has_customer",
            "given": [{"source": "crm", "field": "stage", "equals": "closed_won"}],
            "must_be_true": [{"source": "billing", "field": "customer_exists", "equals": True}],
        },
        "sources": {
            "crm": {"stage": "closed_won"},
            "billing": {"customer_exists": True},
        },
    })
    assert response.status_code == 200
    assert response.json()["status"] == "consistent"


def test_false_given_is_not_applicable():
    response = client.post("/v1/check/employee-offboarding", json={
        "employee_id": "emp_123",
        "hr_status": "active",
        "account_access_active": True,
    })
    assert response.status_code == 200
    assert response.json()["status"] == "not_applicable"


def test_batch_aggregates_violations():
    check = {
        "subject_id": "order_1",
        "invariant": {
            "name": "fulfilled_has_shipment",
            "given": [{"source": "commerce", "field": "status", "equals": "fulfilled"}],
            "must_be_true": [{"source": "fulfilment", "field": "status", "equals": "shipped"}],
        },
        "sources": {
            "commerce": {"status": "fulfilled"},
            "fulfilment": {"status": "pending"},
        },
    }
    response = client.post("/v1/verify-batch", json={"checks": [check, check]})
    assert response.status_code == 200
    assert response.json()["violation_count"] == 2


def test_invalid_operator_shape_is_not_billable_success():
    response = client.post("/v1/verify", json={
        "subject_id": "x",
        "invariant": {
            "name": "bad",
            "must_be_true": [{"source": "one", "field": "value"}],
        },
        "sources": {"one": {"value": 1}},
    })
    assert response.status_code == 422
