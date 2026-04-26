#!/bin/bash

# Deployment Configuration
SERVER_IP="161.118.250.195"
SERVER_USER="root"
SERVER_PORT="22"
SERVER_PASSWORD="Akshay343402355468"
DEPLOY_DIR="/Ashlesha"
REPO_URL="https://github.com/nishkarshk212/lily-X-music.git"
SERVICE_NAME="Ashlesha"
LOGGER_ID="-1003933711900"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ${SERVICE_NAME} Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Install sshpass if not available
if ! command -v sshpass &> /dev/null; then
    echo -e "${YELLOW}Installing sshpass...${NC}"
    if [[ "$(uname)" == "Darwin" ]]; then
        brew install sshpass
    else
        sudo apt-get install -y sshpass
    fi
fi

# SSH command wrapper
SSH_CMD="sshpass -p '${SERVER_PASSWORD}' ssh -o StrictHostKeyChecking=no -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_IP}"
SCP_CMD="sshpass -p '${SERVER_PASSWORD}' scp -o StrictHostKeyChecking=no -P ${SERVER_PORT}"

echo -e "${GREEN}[1/8] Connecting to server...${NC}"
$SSH_CMD "echo 'Connection successful'" || { echo -e "${RED}Failed to connect to server${NC}"; exit 1; }

echo -e "${GREEN}[2/8] Creating deployment directory ${DEPLOY_DIR}...${NC}"
$SSH_CMD "mkdir -p ${DEPLOY_DIR}"

echo -e "${GREEN}[3/8] Cloning repository...${NC}"
$SSH_CMD "cd ${DEPLOY_DIR} && git clone ${REPO_URL} . || (git pull origin main)"

echo -e "${GREEN}[4/8] Setting up environment variables...${NC}"
# Upload .env file
$SCP_CMD .env ${SERVER_USER}@${SERVER_IP}:${DEPLOY_DIR}/.env

echo -e "${GREEN}[5/8] Installing uv and dependencies...${NC}"
$SSH_CMD "cd ${DEPLOY_DIR} && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    export PATH=\$HOME/.local/bin:\$PATH && \
    uv sync"

echo -e "${GREEN}[6/8] Setting up systemd service...${NC}"
$SSH_CMD "cat > /etc/systemd/system/${SERVICE_NAME}.service << 'EOF'
[Unit]
Description=${SERVICE_NAME} Telegram Music Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=${DEPLOY_DIR}
ExecStart=/root/.local/bin/uv run python3 -m lily
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF"

echo -e "${GREEN}[7/8] Setting up log cleanup (2 weeks)...${NC}"
$SSH_CMD "cat > /etc/systemd/system/${SERVICE_NAME}-cleanup.timer << 'EOF'
[Unit]
Description=Cleanup ${SERVICE_NAME} logs older than 2 weeks

[Timer]
OnCalendar=weekly
Persistent=true

[Install]
WantedBy=timers.timer
EOF"

$SSH_CMD "cat > /etc/systemd/system/${SERVICE_NAME}-cleanup.service << 'EOF'
[Unit]
Description=Cleanup ${SERVICE_NAME} logs and unnecessary data

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'find /var/log -name \"*${SERVICE_NAME}*\" -mtime +14 -delete; find ${DEPLOY_DIR} -name \"*.pyc\" -delete; find ${DEPLOY_DIR} -name \"__pycache__\" -type d -exec rm -rf {} + 2>/dev/null || true'
EOF"

$SSH_CMD "systemctl daemon-reload && \
    systemctl enable ${SERVICE_NAME}-cleanup.timer && \
    systemctl start ${SERVICE_NAME}-cleanup.timer"

echo -e "${GREEN}[8/8] Starting ${SERVICE_NAME} service...${NC}"
$SSH_CMD "systemctl daemon-reload && \
    systemctl enable ${SERVICE_NAME} && \
    systemctl restart ${SERVICE_NAME}"

# Wait for service to start
sleep 5

# Get service status
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Status${NC}"
echo -e "${GREEN}========================================${NC}"

$SSH_CMD "systemctl status ${SERVICE_NAME} --no-pager -l"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Service Information${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Service Name: ${SERVICE_NAME}"
echo -e "Directory: ${DEPLOY_DIR}"
echo -e "Server: ${SERVER_USER}@${SERVER_IP}:${SERVER_PORT}"
echo -e "Repository: ${REPO_URL}"
echo ""

# Check if service is running
$SSH_CMD "systemctl is-active ${SERVICE_NAME}" | grep -q "active"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ ${SERVICE_NAME} is running successfully!${NC}"
    
    # Send notification to log group (using curl to Telegram API if BOT_TOKEN is available)
    echo -e "${YELLOW}Sending deployment notification to log group...${NC}"
    $SSH_CMD "cd ${DEPLOY_DIR} && source .env && \
        if [ -n '\$BOT_TOKEN' ]; then \
            curl -s -X POST 'https://api.telegram.org/bot\${BOT_TOKEN}/sendMessage' \
                -d chat_id=${LOGGER_ID} \
                -d parse_mode=HTML \
                -d text='<b>🚀 Service Deployed Successfully</b>%0A%0A<b>Service:</b> ${SERVICE_NAME}%0A<b>Directory:</b> ${DEPLOY_DIR}%0A<b>Server:</b> ${SERVER_IP}%0A<b>Status:</b> ✅ Active%0A<b>Time:</b> \$(date)%0A%0A<b>Auto Cleanup:</b> Enabled (2 weeks)%0A<b>Logs:</b> journalctl -u ${SERVICE_NAME}'; \
        fi"
else
    echo -e "${RED}✗ ${SERVICE_NAME} failed to start. Checking logs...${NC}"
    $SSH_CMD "journalctl -u ${SERVICE_NAME} --no-pager -n 50"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Useful Commands${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "View logs:        sshpass -p '${SERVER_PASSWORD}' ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_IP} 'journalctl -u ${SERVICE_NAME} -f'"
echo -e "Stop service:     sshpass -p '${SERVER_PASSWORD}' ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_IP} 'systemctl stop ${SERVICE_NAME}'"
echo -e "Restart service:  sshpass -p '${SERVER_PASSWORD}' ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_IP} 'systemctl restart ${SERVICE_NAME}'"
echo -e "Service status:   sshpass -p '${SERVER_PASSWORD}' ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_IP} 'systemctl status ${SERVICE_NAME}'"
echo -e "Update service:   sshpass -p '${SERVER_PASSWORD}' ssh -p ${SERVER_PORT} ${SERVER_USER}@${SERVER_IP} 'cd ${DEPLOY_DIR} && git pull && systemctl restart ${SERVICE_NAME}'"
echo ""
