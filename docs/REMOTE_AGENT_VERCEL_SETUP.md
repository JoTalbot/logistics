# Remote Agent + Vercel Control Plane

## Vercel production variables

Set these in Project Settings → Environment Variables for Production:

- `DATABASE_URL` — PostgreSQL connection string for the logistics database.
- `REMOTE_AGENT_TOKEN` — must exactly match the Ubuntu `CONTROL_PLANE_TOKEN` used by the remote agent.
- `CONTROL_PLANE_OPERATOR_TOKEN` — separate long random token used only by the Android/browser console.
- `VERCEL_AUTOMATION_BYPASS_SECRET` — the 32-character secret generated under Deployment Protection → Protection Bypass for Automation. It allows the remote agent to reach protected Vercel deployments using the `x-vercel-protection-bypass` header.

Redeploy after changing environment variables.

## Vercel Deployment Protection

Keep Deployment Protection enabled. Do not disable SSO for the whole project just to support the Ubuntu agent.

Create a dedicated Protection Bypass for Automation secret in the Vercel project and store the same value as the Production `VERCEL_AUTOMATION_BYPASS_SECRET` environment variable.

The Ubuntu agent sends that value only as the `x-vercel-protection-bypass` request header. It is never exposed to browser JavaScript or returned by the agent health endpoint.

## Ubuntu agent variables

In `/etc/logistics-agent/agent.env`:

```env
CONTROL_PLANE_URL=https://logistics-fawn-pi.vercel.app
CONTROL_PLANE_TOKEN=<same value as REMOTE_AGENT_TOKEN>
VERCEL_AUTOMATION_BYPASS_SECRET=<same value as the Vercel automation bypass secret>
AGENT_NAME=arm-server-01
AGENT_HEARTBEAT_SECONDS=30
```

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

If `REMOTE_AGENT_TOKEN` must be added with the Vercel CLI, obtain the existing agent token directly from the protected server environment and pipe it to the interactive CLI. Do not echo it:

```bash
TOKEN="$(sudo awk -F= '/^AGENT_AUTH_TOKEN=/{print substr($0,index($0,"=")+1)}' /etc/logistics-agent/agent.env)"
printf '%s\n' "$TOKEN" | vercel env add REMOTE_AGENT_TOKEN production
unset TOKEN
```

The CLI may ask for project/scope if the local directory is not linked. Use the existing `fgfgggg/logistics` project.

## Browser

Open the production project URL. The root page is the mobile-friendly Logistics Control Plane. Enter `CONTROL_PLANE_OPERATOR_TOKEN`; it is stored only in the browser's local storage and sent as an Authorization header.

## Security boundary

- The Ubuntu agent makes outbound HTTPS connections to Vercel.
- No public `8787` listener is required.
- The Vercel console never receives the Ubuntu SSH private key.
- Commands are still constrained by the agent allowlist and shell-composition protection.
- High-risk command patterns are marked `REVIEW` and are not dispatched automatically.
- V21 business autonomy/approval controls remain independent of this infrastructure control plane.
