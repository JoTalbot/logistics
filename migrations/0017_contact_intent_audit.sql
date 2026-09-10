CREATE TABLE IF NOT EXISTS contact_intent_audit (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    contact_intent_id uuid NOT NULL REFERENCES contact_intents(id) ON DELETE CASCADE,
    action text NOT NULL CHECK (action IN ('approve','reject','hold')),
    resulting_status text NOT NULL CHECK (resulting_status IN ('pending','approved','rejected')),
    operator_ref text NOT NULL CHECK (length(trim(operator_ref)) > 0),
    reason text NOT NULL CHECK (length(trim(reason)) > 0),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_contact_intent_audit_review
    ON contact_intent_audit (tenant_id, contact_intent_id, created_at DESC);
