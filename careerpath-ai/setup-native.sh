#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# CareerPath AI — Setup Script (Native Linux/WSL2)
# ═══════════════════════════════════════════════════════════════════════════
# Usage: chmod +x setup.sh && ./setup.sh install
#        ./setup.sh start

set -e

PROJECT_ROOT="/path/to/careerpath-ai"  # Modifica asta cu path-ul real
ACTION="${1:-install}"

# ═══════════════════════════════════════════════════════════════════════════
# COLORS & OUTPUT
# ═══════════════════════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

write_header() {
    echo -e "\n${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║ $1${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
}

write_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

write_error() {
    echo -e "${RED}❌ $1${NC}"
}

write_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════
# INSTALL DEPENDENCIES
# ═══════════════════════════════════════════════════════════════════════════

install_dependencies() {
    write_header "STEP 1: Checking Prerequisites"

    # Check Node.js
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        write_success "Node.js $NODE_VERSION found"
    else
        write_error "Node.js not found"
        echo "Install: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt install -y nodejs"
        exit 1
    fi

    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        write_success "$PYTHON_VERSION found"
    else
        write_error "Python 3 not found"
        echo "Install: sudo apt install -y python3 python3-pip python3-venv"
        exit 1
    fi

    # Check PostgreSQL
    if command -v psql &> /dev/null; then
        PG_VERSION=$(psql --version)
        write_success "$PG_VERSION found"
    else
        write_error "PostgreSQL not found"
        echo "Install: sudo apt install -y postgresql postgresql-contrib"
        exit 1
    fi

    # Check Redis
    if command -v redis-cli &> /dev/null; then
        REDIS_VERSION=$(redis-cli --version)
        write_success "$REDIS_VERSION found"
    else
        write_error "Redis not found"
        echo "Install: sudo apt install -y redis-server"
        exit 1
    fi

    write_header "STEP 2: Installing Node Dependencies"

    # API Gateway
    write_info "Building api-gateway..."
    cd "$PROJECT_ROOT/api-gateway"
    npm install > /dev/null 2>&1
    npm run build > /dev/null 2>&1
    write_success "api-gateway ready"

    # Frontend
    write_info "Installing frontend..."
    cd "$PROJECT_ROOT/frontend"
    npm install > /dev/null 2>&1
    write_success "frontend ready"

    write_header "STEP 3: Setting Up Python Virtual Environments"

    SERVICES=(
        "services/cv-analyzer-agent"
        "services/hr-interview-agent"
        "services/agent-orchestrator"
    )

    for service in "${SERVICES[@]}"; do
        SERVICE_PATH="$PROJECT_ROOT/$service"
        write_info "Setting up $service..."

        if [ -d "$SERVICE_PATH/.venv" ]; then
            write_info "  Virtual env already exists, skipping..."
        else
            cd "$SERVICE_PATH"
            python3 -m venv .venv
            source .venv/bin/activate
            pip install -q -r requirements.txt
            deactivate
            write_success "  ✓ $service ready"
        fi
    done

    write_header "✅ INSTALLATION COMPLETE"
    echo "Next step: ./setup.sh start"
}

# ═══════════════════════════════════════════════════════════════════════════
# START SERVICES
# ═══════════════════════════════════════════════════════════════════════════

start_services() {
    write_header "STARTING CareerPath AI Services"

    # Check .env
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        write_error ".env not found!"
        write_info "Run: cd $PROJECT_ROOT && cp .env.example .env"
        exit 1
    fi

    # PostgreSQL
    write_header "Starting PostgreSQL"
    if sudo service postgresql status > /dev/null 2>&1; then
        write_success "PostgreSQL already running"
    else
        sudo service postgresql start
        write_success "PostgreSQL started"
    fi
    sleep 2

    # Redis
    write_header "Starting Redis"
    if pgrep -x "redis-server" > /dev/null; then
        write_success "Redis already running"
    else
        redis-server --daemonize yes
        write_success "Redis started"
    fi
    sleep 2

    # API Gateway
    write_header "Starting API Gateway (NestJS)"
    write_info "Terminal will open in tmux..."
    tmux new-session -d -s api-gateway -c "$PROJECT_ROOT/api-gateway" \
        "npm run start:dev"
    write_success "API Gateway started (tmux: api-gateway)"

    sleep 3

    # Frontend
    write_header "Starting Frontend (Next.js)"
    write_info "Terminal will open in tmux..."
    tmux new-session -d -s frontend -c "$PROJECT_ROOT/frontend" \
        "npm run dev"
    write_success "Frontend started (tmux: frontend)"

    sleep 2

    # Agents
    declare -A AGENTS=(
        ["CV Analyzer"]="services/cv-analyzer-agent:8002"
        ["HR Interview"]="services/hr-interview-agent:8003"
        ["Agent Orchestrator"]="services/agent-orchestrator:8005"
    )

    for agent_name in "${!AGENTS[@]}"; do
        IFS=':' read -r agent_path agent_port <<< "${AGENTS[$agent_name]}"
        write_header "Starting $agent_name"
        write_info "Terminal will open in tmux..."

        tmux new-session -d -s "${agent_name,,}" -c "$PROJECT_ROOT/$agent_path" \
            "source .venv/bin/activate && uvicorn src.main:app --port $agent_port --reload"

        write_success "$agent_name started (tmux: ${agent_name,,})"
        sleep 1
    done

    write_header "✅ ALL SERVICES STARTED"
    cat << EOF

📊 Access Points:
   Frontend        → http://localhost:3000
   API Gateway     → http://localhost:8000/health
   CV Analyzer     → http://localhost:8002/docs
   HR Interview    → http://localhost:8003/docs
   Orchestrator    → http://localhost:8005/docs
   PostgreSQL      → localhost:5432
   Redis           → localhost:6379

🖥️  Tmux Sessions:
   tmux attach-session -t api-gateway
   tmux attach-session -t frontend
   tmux attach-session -t cv analyzer
   tmux attach-session -t hr interview
   tmux attach-session -t agent orchestrator

💡 Tip: tmux list-sessions to see all running sessions
EOF
}

# ═══════════════════════════════════════════════════════════════════════════
# STOP SERVICES
# ═══════════════════════════════════════════════════════════════════════════

stop_services() {
    write_header "STOPPING CareerPath AI Services"

    # Kill tmux sessions
    write_info "Stopping tmux sessions..."
    tmux list-sessions 2>/dev/null | grep -E "(api-gateway|frontend|cv analyzer|hr interview|agent orchestrator)" | awk '{print $1}' | sed 's/:$//' | while read session; do
        tmux kill-session -t "$session" 2>/dev/null && write_success "Killed $session"
    done

    # Kill Node processes
    pkill -f "npm run" || true
    write_success "Node services stopped"

    # Kill Python processes
    pkill -f "uvicorn" || true
    write_success "Python agents stopped"

    write_success "All services stopped"
}

# ═══════════════════════════════════════════════════════════════════════════
# CHECK STATUS
# ═══════════════════════════════════════════════════════════════════════════

check_status() {
    write_header "SERVICE STATUS"

    # Check HTTP endpoints
    endpoints=(
        "API Gateway:http://localhost:8000/health"
        "Frontend:http://localhost:3000"
        "CV Analyzer:http://localhost:8002/docs"
        "HR Interview:http://localhost:8003/docs"
        "Orchestrator:http://localhost:8005/docs"
    )

    for endpoint in "${endpoints[@]}"; do
        IFS=':' read -r name url <<< "$endpoint"
        if curl -s "$url" > /dev/null 2>&1; then
            write_success "$name ✓"
        else
            write_error "$name ✗"
        fi
    done

    # Check ports
    write_info "\nDatabase & Cache:"
    if nc -z localhost 5432 2>/dev/null; then
        write_success "PostgreSQL ✓"
    else
        write_error "PostgreSQL ✗"
    fi

    if nc -z localhost 6379 2>/dev/null; then
        write_success "Redis ✓"
    else
        write_error "Redis ✗"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# CLEAN
# ═══════════════════════════════════════════════════════════════════════════

clean_environment() {
    write_header "CLEANING UP"

    write_info "Removing Python virtual environments..."
    SERVICES=(
        "services/cv-analyzer-agent"
        "services/hr-interview-agent"
        "services/agent-orchestrator"
    )

    for service in "${SERVICES[@]}"; do
        VENV_PATH="$PROJECT_ROOT/$service/.venv"
        if [ -d "$VENV_PATH" ]; then
            rm -rf "$VENV_PATH"
            write_success "  Removed $service/.venv"
        fi
    done

    write_info "Clearing Redis..."
    redis-cli FLUSHALL > /dev/null 2>&1
    write_success "Redis cleared"

    write_success "Cleanup complete"
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

case "$ACTION" in
    install)
        install_dependencies
        ;;
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    status)
        check_status
        ;;
    clean)
        clean_environment
        ;;
    *)
        echo "Usage: $0 <action>"
        echo ""
        echo "Actions:"
        echo "  install    - Install all dependencies (run first time)"
        echo "  start      - Start all services"
        echo "  stop       - Stop all services"
        echo "  status     - Check service status"
        echo "  clean      - Clean up virtual environments"
        echo ""
        echo "Example:"
        echo "  chmod +x setup.sh"
        echo "  ./setup.sh install"
        echo "  ./setup.sh start"
        ;;
esac

