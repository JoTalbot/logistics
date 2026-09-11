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
ExecStart=$AGENT_DIR/.venv/bin/uvicorn agent:APP --host 127.0.0.1 --port 8787
Restart=always
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$AGENT_DIR /var/lib/logistics-agent $REPO_DIR

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE"

if grep -q 'generate-a-long-random-secret' "$ENV_DIR/agent.env" || grep -q 'replace-with-vercel-ai-gateway-key' "$ENV_DIR/agent.env"; then
  echo "Service installed but NOT started because secrets are still placeholders."
  echo "Edit: $ENV_DIR/agent.env"
  echo "Then run: systemctl restart $SERVICE"
else
  systemctl restart "$SERVICE"
  sleep 2
  curl -fsS http://127.0.0.1:8787/health
  echo
fi

echo "Remote agent installation complete."
