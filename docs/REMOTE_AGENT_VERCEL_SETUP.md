# Remote Agent + Vercel Control Plane

## Vercel production variables

Set these in Project Settings → Environment Variables for Production:

- `DATABASE_URL` — PostgreSQL connection string for the logistics database.
- `REMOTE_AGENT_TOKEN` — bootstrap/enrollment credential used only when an agent starts without a per-agent credential. It is not accepted for task polling, events, or completion after enrollment.
- `CONTROL_PLANE_OPERATOR_TOKEN` — separate long random token used only by the Android/browser console.
- `VERCEL_AUTOMATION_BYPASS_SECRET` — the 32-character secret generated under Deployment Protection → Protection Bypass for Automation. It allows the remote agent to reach protected Vercel deployments using the `x-vercel-protection-bypass` header.

Redeploy after changing environment variables.

## Per-agent credential model

Each row in `remote_agents` has a SHA-256 hash of its current control credential. Plaintext agent credentials are never stored in PostgreSQL.

On first startup, an agent authenticates with the bootstrap `REMOTE_AGENT_TOKEN` without an `agent_id`. The control plane registers or re-enrolls the agent by name and returns a freshly generated `control_token`. The running agent keeps that credential in memory and uses it for subsequent heartbeat, task polling, event, and completion calls.

If the agent process restarts, it bootstraps again without an `agent_id`; the server rotates the per-agent credential and returns the new value. The bootstrap credential therefore acts as an enrollment credential, while normal task lifecycle traffic is bound to the individual agent credential.

Do not treat `REMOTE_AGENT_TOKEN` as a per-agent secret. Protect it like an enrollment/admin credential and rotate it if exposed.

## Vercel Deployment Protection

Keep Deployment Protection enabled. Do not disable SSO for the whole project just to support the Ubuntu agent.

Create a dedicated Protection Bypass for Automation secret in the Vercel project and store the same value as the Production `VERCEL_AUTOMATION_BYPASS_SECRET` environment variable.

The Ubuntu agent sends that value only as the `x-vercel-protection-bypass` request header. It is never exposed to browser JavaScript or returned by the agent health endpoint.

## Ubuntu agent variables

In `/etc/logistics-agent/agent.env`:

```env
CONTROL_PLANE_URL=<current Vercel production URL for the logistics project>
CONTROL_PLANE_TOKEN=<same value as REMOTE_AGENT_TOKEN>
# Optional: pre-provision a per-agent credential. Otherwise bootstrap is automatic.
CONTROL_AGENT_TOKEN=<per-agent control token, when pre-provisioned>
VERCEL_AUTOMATION_BYPASS_SECRET=<same value as the Vercel automation bypass secret>
AGENT_NAME=arm-server-01
AGENT_HEARTBEAT_SECONDS=30
```

Do not hard-code a historical Vercel deployment URL here. Resolve and record the current production URL from the active Vercel project before configuring the agent.

Do not expose these values in Git or browser JavaScript.

## One-time Ubuntu sync

```bash
sudo systemctl stop logistics-agent || true
cd /opt/logistics
sudo git fetch origin main
sudo git reset --hard origin/main
sudo install -o logistics-agent -g logistics-agent -m 0755 deploy/remote-agent/agent.py /opt/logistics-agent/agent.py
sudo -u logistics-agent /opt/logistics-agent/.venv/bin/python -m py_compile /opt/logistics-agent/agent.py
sudo systemctl daemon-reload
sudo systemctl restart logistics-agent
sudo systemctl status logistics-agent --no-pager
curl -sS http://127.0.0.1:8787/health
```

## Token handoff without printing the token

The bootstrap credential must be present in the protected Vercel environment and in the agent environment for automatic enrollment. Do not print either credential. If a credential must be added with the Vercel CLI, pipe it to the interactive command and unset the shell variable immediately afterwards.

```bash
TOKEN="$(sudo awk -F= '/^CONTROL_PLANE_TOKEN=/{print substr($0,index($0,"=")+1)}' /etc/logistics-agent/agent.env)"
printf '%s\n' "$TOKEN" | vercel env add REMOTE_AGENT_TOKEN production
unset TOKEN
```

The CLI may ask for project/scope if the local directory is not linked. Use the existing logistics Vercel project.

## Browser

Open the current production project URL. The root page is the mobile-friendly Logistics Control Plane. Enter `CONTROL_PLANE_OPERATOR_TOKEN`; it is stored only in the browser's local storage and sent as an Authorization header.

## Security boundary

- The Ubuntu agent makes outbound HTTPS connections to Vercel.
- No public `8787` listener is required.
- The Vercel console never receives the Ubuntu SSH private key.
- Task polling, task events, and completion require the credential belonging to the target agent.
- A wrong agent credential cannot operate another agent's task.
- Credentials are hashed at rest and rotated on bootstrap enrollment.
- Commands are still constrained by the agent allowlist and shell-composition protection.
- High-risk command patterns are marked `REVIEW` and are not dispatched automatically.
- V21 business autonomy/approval controls remain independent of this infrastructure control plane.
- This setup does not bypass provider protections or authorization gates.
