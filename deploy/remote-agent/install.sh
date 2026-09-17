#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${LOGISTICS_REPO_DIR:-/opt/logistics}"
AGENT_DIR="${LOGISTICS_AGENT_DIR:-/opt/logistics-agent}"
ENV_DIR="/etc/logistics-agent"
SERVICE="logistics-agent.service"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root: sudo $0"
  exit 1
fi

command -v git >/dev/null || { echo "git is required"; exit 1; }
command -v python3 >/dev/null || { echo "python3 is required"; exit 1; }

if [[ ! -d "$REPO_DIR/.git" ]]; then
  git clone https://github.com/JoTalbot/logistics.git "$REPO_DIR"
else
  git -C "$REPO_DIR" fetch origin main
  git -C "$REPO_DIR" checkout main
  git -C "$REPO_DIR" pull --ff-only origin main
fi

id -u logistics-agent >/dev/null 2>&1 || useradd --system --create-home --shell /usr/sbin/nologin logistics-agent
install -d -o logistics-agent -g logistics-agent "$AGENT_DIR"
install -d -o logistics-agent -g logistics-agent /var/lib/logistics-agent
# The cgroup rehearsal is non-root and writes machine-readable evidence as the
# service identity. Prepare the persistent evidence directory at install time
# so the agent never needs to create a system-owned path itself.
install -d -o logistics-agent -g logistics-agent -m 0750 /var/lib/logistics-agent/evidence
install -d -m 0750 "$ENV_DIR"

python3 -m venv "$AGENT_DIR/.venv"
"$AGENT_DIR/.venv/bin/pip" install --upgrade pip
"$AGENT_DIR/.venv/bin/pip" install -r "$REPO_DIR/deploy/remote-agent/requirements.txt"
install -m 0750 "$REPO_DIR/deploy/remote-agent/agent.py" "$AGENT_DIR/agent.py"
chown -R logistics-agent:logistics-agent "$AGENT_DIR" /var/lib/logistics-agent

if [[ ! -f "$ENV_DIR/agent.env" ]]; then
  install -m 0600 "$REPO_DIR/deploy/remote-agent/.env.example" "$ENV_DIR/agent.env"
  echo
  echo "Created $ENV_DIR/agent.env"
  echo "IMPORTANT: edit it and replace AGENT_AUTH_TOKEN and AI_GATEWAY_API_KEY before starting the service."
else
  echo "$ENV_DIR/agent.env already exists; preserving it."
fi

cat > /etc/systemd/system/$SERVICE <<EOF
[Unit]
Description=Logistics Ubuntu Remote Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=logistics-agent
Group=logistics-agent
WorkingDirectory=$AGENT_DIR
EnvironmentFile=$ENV_DIR/agent.env
# Enforce the same fail-closed credential boundary at every service start,
# including reboot/manual restart. Do not rely only on installer-time checks.
ExecStartPre=/usr/bin/bash -c 'test -n "$${AGENT_AUTH_TOKEN}" && test -n "$${AI_GATEWAY_API_KEY}" && test "$${AGENT_AUTH_TOKEN}" != "generate-a-long-random-secret" && test "$${AI_GATEWAY_API_KEY}" != "replace-with-vercel-ai-gateway-key" && test "$${CONTROL_PLANE_URL}" != "<current Vercel production URL for the logistics project>" && test "$${CONTROL_PLANE_TOKEN}" != "use-the-same-secret-as-Vercel-REMOTE_AGENT_TOKEN" && { { test -z "$${CONTROL_PLANE_URL}" && test -z "$${CONTROL_PLANE_TOKEN}"; } || { test -n "$${CONTROL_PLANE_URL}" && test -n "$${CONTROL_PLANE_TOKEN}"; }; }'
ExecStart=$AGENT_DIR/.venv/bin/uvicorn agent:APP --host 127.0.0.1 --port 8787
Restart=always
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
# Keep the whole agent subtree together on service stop/restart. This is a
# service-level safety net; per-task lease fencing remains agent-controlled.
KillMode=control-group
# Delegate a private cgroup subtree so a future per-task supervisor can fence
# descendants that deliberately create independent sessions/process groups.
Delegate=yes
TasksMax=512
LimitNOFILE=8192
ReadWritePaths=$AGENT_DIR /var/lib/logistics-agent $REPO_DIR

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE"

# Never start with missing required credentials. Do not source agent.env here:
# it is untrusted configuration and must not become shell code at install time.
required_credentials_missing=0
if ! awk -F= '
  $1 == "AGENT_AUTH_TOKEN" && $2 !~ /^[[:space:]]*$/ { found=1 }
  END { exit(found ? 0 : 1) }
' "$ENV_DIR/agent.env"; then
  required_credentials_missing=1
fi
if ! awk -F= '
  $1 == "AI_GATEWAY_API_KEY" && $2 !~ /^[[:space:]]*$/ { found=1 }
  END { exit(found ? 0 : 1) }
' "$ENV_DIR/agent.env"; then
  required_credentials_missing=1
fi

control_url_configured=0
control_token_configured=0
if awk -F= '$1 == "CONTROL_PLANE_URL" && $2 !~ /^[[:space:]]*$/ { found=1 } END { exit(found ? 0 : 1) }' "$ENV_DIR/agent.env"; then
  control_url_configured=1
fi
if awk -F= '$1 == "CONTROL_PLANE_TOKEN" && $2 !~ /^[[:space:]]*$/ { found=1 } END { exit(found ? 0 : 1) }' "$ENV_DIR/agent.env"; then
  control_token_configured=1
fi

placeholder_found=0
if grep -Eq 'generate-a-long-random-secret|replace-with-vercel-ai-gateway-key|<current Vercel production URL for the logistics project>|use-the-same-secret-as-Vercel-REMOTE_AGENT_TOKEN' "$ENV_DIR/agent.env"; then
  placeholder_found=1
fi

control_pair_incomplete=0
if [[ "$control_url_configured" -ne "$control_token_configured" ]]; then
  control_pair_incomplete=1
fi

if [[ "$required_credentials_missing" -ne 0 || "$placeholder_found" -ne 0 || "$control_pair_incomplete" -ne 0 ]]; then
  echo "Service installed but NOT started because required credentials or control-plane settings are incomplete."
  echo "Edit: $ENV_DIR/agent.env"
  echo "Required: non-empty AGENT_AUTH_TOKEN and AI_GATEWAY_API_KEY."
  echo "CONTROL_PLANE_URL and CONTROL_PLANE_TOKEN must either both be set or both be empty."
  echo "Then run: systemctl restart $SERVICE"
else
  systemctl restart "$SERVICE"
  sleep 2
  curl -fsS http://127.0.0.1:8787/health
  echo
fi

echo "Remote agent installation complete."
