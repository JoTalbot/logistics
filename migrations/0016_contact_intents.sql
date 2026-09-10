CREATE TABLE IF NOT EXISTS contact_intents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    prospect_id uuid NOT NULL REFERENCES customer_prospects(id) ON DELETE CASCADE,
    channel text NOT NULL CHECK (channel IN ('email','telegram','phone','web_form')),
    target text NOT NULL CHECK (length(trim(target)) > 0),
    message text NOT NULL CHECK (length(trim(message)) > 0),
    authorized boolean NOT NULL DEFAULT false,
    suppressed boolean NOT NULL DEFAULT false,
    human_approval_required boolean NOT NULL DEFAULT true,
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected','sent','suppressed')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, prospect_id, channel, target)
);

CREATE INDEX IF NOT EXISTS idx_contact_intents_review
    ON contact_intents (tenant_id, status, created_at ASC);
