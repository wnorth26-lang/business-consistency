from business_consistency.engine import evaluate

CFG={"invariants":[{"name":"paid_customer_has_access","entity":"cus_123","given":[{"source":"stripe","field":"subscription.status","equals":"active"}],"must_be_true":[{"source":"product_db","field":"user.plan","equals":"pro"}]}]}

def test_detects_state_violation():
    out=evaluate(CFG,{"stripe":{"subscription":{"status":"active"}},"product_db":{"user":{"plan":"free"}}})
    assert len(out)==1 and out[0].observed=="free" and out[0].expected=="pro"

def test_passes_consistent_state():
    assert evaluate(CFG,{"stripe":{"subscription":{"status":"active"}},"product_db":{"user":{"plan":"pro"}}})==[]

def test_given_scopes_invariant():
    assert evaluate(CFG,{"stripe":{"subscription":{"status":"cancelled"}},"product_db":{"user":{"plan":"free"}}})==[]
