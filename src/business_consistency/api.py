"""Stateless HTTP API for supplied-state business consistency checks."""

from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from business_consistency.engine import evaluate


BILLING_DESCRIPTION = (
    "Marketplace billing is enforced by the hosting gateway. Validation failures and "
    "internal errors must never settle usage."
)


class Condition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1, max_length=100)
    field: str = Field(min_length=1, max_length=250)
    equals: Any | None = None
    not_equals: Any | None = None
    gt: Any | None = None
    gte: Any | None = None
    lt: Any | None = None
    lte: Any | None = None

    @model_validator(mode="after")
    def exactly_one_operator(self):
        values = [
            self.equals, self.not_equals, self.gt,
            self.gte, self.lt, self.lte,
        ]
        if sum(value is not None for value in values) != 1:
            raise ValueError("exactly one comparison operator is required")
        return self


class Invariant(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=150)
    entity: str | None = Field(default=None, max_length=250)
    severity: Literal["low", "medium", "high", "critical"] = "high"
    given: list[Condition] = Field(default_factory=list, max_length=25)
    must_be_true: list[Condition] = Field(min_length=1, max_length=25)


class VerifyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subject_id: str = Field(min_length=1, max_length=250)
    invariant: Invariant
    sources: dict[str, dict[str, Any]] = Field(min_length=1, max_length=25)


class BatchVerifyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    checks: list[VerifyIn] = Field(min_length=1, max_length=100)


class SubscriptionAccessIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_id: str = Field(min_length=1, max_length=250)
    billing_status: str = Field(min_length=1, max_length=100)
    access_plan: str = Field(min_length=1, max_length=100)
    expected_access_plan: str = Field(default="pro", min_length=1, max_length=100)
    active_billing_status: str = Field(default="active", min_length=1, max_length=100)


class OrderFulfilmentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str = Field(min_length=1, max_length=250)
    commerce_status: str = Field(min_length=1, max_length=100)
    fulfilment_status: str = Field(min_length=1, max_length=100)
    trigger_status: str = Field(default="fulfilled", min_length=1, max_length=100)
    expected_fulfilment_status: str = Field(default="shipped", min_length=1, max_length=100)


class CrmBillingIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    account_id: str = Field(min_length=1, max_length=250)
    crm_stage: str = Field(min_length=1, max_length=100)
    billing_customer_exists: bool
    trigger_stage: str = Field(default="closed_won", min_length=1, max_length=100)


class EmployeeOffboardingIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    employee_id: str = Field(min_length=1, max_length=250)
    hr_status: str = Field(min_length=1, max_length=100)
    account_access_active: bool
    terminated_status: str = Field(default="terminated", min_length=1, max_length=100)


def _condition_dict(condition: Condition) -> dict[str, Any]:
    return condition.model_dump(exclude_none=True)


def verify(payload: VerifyIn) -> dict[str, Any]:
    invariant = payload.invariant.model_dump(exclude_none=True)
    invariant["entity"] = invariant.get("entity") or payload.subject_id
    invariant["given"] = [_condition_dict(item) for item in payload.invariant.given]
    invariant["must_be_true"] = [
        _condition_dict(item) for item in payload.invariant.must_be_true
    ]
    try:
        violations = evaluate({"invariants": [invariant]}, payload.sources)
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    applicable = True
    if invariant["given"]:
        scoped = dict(invariant)
        scoped["must_be_true"] = []
        try:
            # An invariant with a false `given` condition produces no violation.
            # Evaluate the conditions directly through a deliberately false assertion.
            probe = dict(invariant)
            probe["must_be_true"] = [
                {"source": next(iter(payload.sources)), "field": "__probe__", "equals": True}
            ]
            probe_sources = {key: dict(value) for key, value in payload.sources.items()}
            probe_sources[next(iter(probe_sources))]["__probe__"] = False
            applicable = bool(evaluate({"invariants": [probe]}, probe_sources))
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    status = "violation" if violations else ("consistent" if applicable else "not_applicable")
    return {
        "subject_id": payload.subject_id,
        "invariant": invariant["name"],
        "status": status,
        "verified": status == "consistent",
        "applicable": applicable,
        "violation_count": len(violations),
        "violations": [item.to_dict() for item in violations],
        "evidence": {"sources": payload.sources, "rule": invariant},
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


app = FastAPI(
    title="Business Consistency API",
    version="0.2.0",
    description=(
        "Deterministic, read-only business state verification. Callers supply current "
        "state; this API does not connect to, store credentials for, or mutate source systems."
    ),
)


@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok", "service": "business-consistency"}


@app.post(
    "/v1/verify",
    summary="Evaluate one supplied-state business invariant",
    description=f"Generic read-only verifier for state supplied by the caller. {BILLING_DESCRIPTION}",
)
def verify_endpoint(payload: VerifyIn):
    return verify(payload)


@app.post(
    "/v1/verify-batch",
    summary="Evaluate up to 100 supplied-state business invariants",
    description=f"Batch form of the generic verifier. {BILLING_DESCRIPTION}",
)
def verify_batch(payload: BatchVerifyIn):
    results = [verify(check) for check in payload.checks]
    return {
        "status": "violation" if any(x["status"] == "violation" for x in results) else "consistent",
        "check_count": len(results),
        "violation_count": sum(x["violation_count"] for x in results),
        "results": results,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@app.post(
    "/v1/check/subscription-access",
    summary="Check that an active subscription has the expected product access",
    description=f"Stripe-versus-product-database style consistency check. {BILLING_DESCRIPTION}",
)
def subscription_access(payload: SubscriptionAccessIn):
    return verify(VerifyIn(
        subject_id=payload.customer_id,
        invariant=Invariant(
            name="paid_customer_has_access",
            given=[Condition(source="billing", field="status", equals=payload.active_billing_status)],
            must_be_true=[Condition(source="product", field="plan", equals=payload.expected_access_plan)],
            severity="critical",
        ),
        sources={"billing": {"status": payload.billing_status}, "product": {"plan": payload.access_plan}},
    ))


@app.post(
    "/v1/check/order-fulfilment",
    summary="Check that a fulfilled commerce order has a matching shipment state",
    description=f"Commerce-versus-fulfilment consistency check. {BILLING_DESCRIPTION}",
)
def order_fulfilment(payload: OrderFulfilmentIn):
    return verify(VerifyIn(
        subject_id=payload.order_id,
        invariant=Invariant(
            name="fulfilled_order_has_shipment",
            given=[Condition(source="commerce", field="status", equals=payload.trigger_status)],
            must_be_true=[Condition(source="fulfilment", field="status", equals=payload.expected_fulfilment_status)],
            severity="high",
        ),
        sources={"commerce": {"status": payload.commerce_status}, "fulfilment": {"status": payload.fulfilment_status}},
    ))


@app.post(
    "/v1/check/crm-billing",
    summary="Check that a closed-won CRM account exists in billing",
    description=f"CRM-versus-billing consistency check. {BILLING_DESCRIPTION}",
)
def crm_billing(payload: CrmBillingIn):
    return verify(VerifyIn(
        subject_id=payload.account_id,
        invariant=Invariant(
            name="closed_won_account_exists_in_billing",
            given=[Condition(source="crm", field="stage", equals=payload.trigger_stage)],
            must_be_true=[Condition(source="billing", field="customer_exists", equals=True)],
            severity="high",
        ),
        sources={"crm": {"stage": payload.crm_stage}, "billing": {"customer_exists": payload.billing_customer_exists}},
    ))


@app.post(
    "/v1/check/employee-offboarding",
    summary="Check that a terminated employee no longer has active account access",
    description=f"HR-versus-identity-provider consistency check. {BILLING_DESCRIPTION}",
)
def employee_offboarding(payload: EmployeeOffboardingIn):
    return verify(VerifyIn(
        subject_id=payload.employee_id,
        invariant=Invariant(
            name="terminated_employee_has_no_access",
            given=[Condition(source="hr", field="status", equals=payload.terminated_status)],
            must_be_true=[Condition(source="identity", field="access_active", equals=False)],
            severity="critical",
        ),
        sources={"hr": {"status": payload.hr_status}, "identity": {"access_active": payload.account_access_active}},
    ))


def run():
    import uvicorn

    uvicorn.run("business_consistency.api:app", host="0.0.0.0", port=8000)
