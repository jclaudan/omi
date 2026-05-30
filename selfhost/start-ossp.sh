#!/bin/bash
set -euo pipefail

# ============================================
# Start Omi OSS+ Stack (Linux/macOS)
# ============================================
# Usage: ./start-ossp.sh [OPTIONS]
# Options:
#   --no-logs    Don't follow logs after startup
#   --help       Show this message

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
NO_LOGS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-logs)
            NO_LOGS=true
            shift
            ;;
        --help)
            cat << 'EOF'
Start Omi OSS+ Stack with Docker Compose

Usage: ./start-ossp.sh [OPTIONS]

Options:
  --no-logs    Don't follow logs after startup
  --help       Show this message

Services started:
  - Supabase (PostgreSQL + PostgREST)
  - Qdrant (Vector Database)
  - MinIO (Object Storage)
  - Faster-Whisper (Speech-to-Text)
  - Ollama (LLM)
  - Redis (Cache)

After startup, services will be available at:
  PostgreSQL:       localhost:5432
  Supabase Studio:  http://localhost:3000
  PostgREST API:    http://localhost:8000
  Qdrant API:       http://localhost:6333
  MinIO Console:    http://localhost:9001
  MinIO API:        http://localhost:9000
  Faster-Whisper:   http://localhost:8001
  Ollama API:       http://localhost:11434
  Redis:            localhost:6379
EOF
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🚀 Starting Omi OSS+ Stack...${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found. Please install Docker.${NC}"
    echo -e "${YELLOW}  For Ubuntu/Debian: sudo apt-get install docker.io docker-compose${NC}"
    echo -e "${YELLOW}  For other systems: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker found: $(docker --version)${NC}"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker Compose found${NC}"

# Generate .env if it doesn't exist
ENV_FILE="$SCRIPT_DIR/.env"
ENV_TEMPLATE="$SCRIPT_DIR/.env.template"

if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$ENV_TEMPLATE" ]; then
        echo -e "${YELLOW}📝 Generating .env file...${NC}"
        cp "$ENV_TEMPLATE" "$ENV_FILE"

        # Generate random secrets
        JWT_SECRET=$(openssl rand -hex 32)
        ENCRYPTION_SECRET=$(openssl rand -hex 32)

        # Update .env with generated secrets
        if command -v sed &> /dev/null; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" "$ENV_FILE"
                sed -i '' "s/ENCRYPTION_SECRET=.*/ENCRYPTION_SECRET=$ENCRYPTION_SECRET/" "$ENV_FILE"
            else
                # Linux
                sed -i "s/JWT_SECRET=.*/JWT_SECRET=$JWT_SECRET/" "$ENV_FILE"
                sed -i "s/ENCRYPTION_SECRET=.*/ENCRYPTION_SECRET=$ENCRYPTION_SECRET/" "$ENV_FILE"
            fi
        fi

        echo -e "${GREEN}✓ .env file created with secure defaults${NC}"
    else
        echo -e "${YELLOW}⚠ .env.template not found${NC}"
    fi
else
    echo -e "${GREEN}✓ Using existing .env file${NC}"
fi

# Pull latest images
echo -e "\n${YELLOW}📦 Pulling latest Docker images...${NC}"
docker-compose -f "$SCRIPT_DIR/docker-compose.yml" pull 2>&1 | tail -20

# Start services
echo -e "\n${YELLOW}▶️  Starting services...${NC}"
docker-compose -f "$SCRIPT_DIR/docker-compose.yml" up -d 2>&1 | grep -E "Creating|Starting|Created|Started" || true

if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo -e "${RED}✗ Failed to start services${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Services started${NC}"

# Wait for services to be healthy
echo -e "\n${YELLOW}⏳ Waiting for services to be healthy...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    # Check if services are running
    RUNNING=$(docker-compose -f "$SCRIPT_DIR/docker-compose.yml" ps --services --filter "status=running" | wc -l)

    if [ $RUNNING -ge 6 ]; then
        echo -e "${GREEN}✓ All services are running${NC}"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo -e "${CYAN}  Waiting... ($RETRY_COUNT/$MAX_RETRIES)${NC}"
    sleep 2
done

# Display service URLs
echo -e "\n${CYAN}📋 OSS+ Services Ready!${NC}\n"
echo -e "${YELLOW}Services:${NC}"
echo -e "  ${CYAN}🐘 PostgreSQL (Supabase)  : localhost:5432${NC}"
echo -e "  ${CYAN}🌐 Supabase Studio       : http://localhost:3000${NC}"
echo -e "  ${CYAN}📡 PostgREST API         : http://localhost:8000${NC}"
echo -e "  ${CYAN}🔍 Qdrant Vector DB      : http://localhost:6333${NC}"
echo -e "  ${CYAN}💾 MinIO Console         : http://localhost:9001${NC}"
echo -e "     MinIO API             : http://localhost:9000${NC}"
echo -e "  ${CYAN}🎤 Faster-Whisper STT    : http://localhost:8001${NC}"
echo -e "     WebSocket (STT)       : ws://localhost:8002${NC}"
echo -e "  ${CYAN}🤖 Ollama LLM            : http://localhost:11434${NC}"
echo -e "  ${CYAN}📦 Redis Cache           : localhost:6379${NC}"

echo -e "\n${YELLOW}Configuration:${NC}"
echo -e "  .env file: $ENV_FILE"

echo -e "\n${YELLOW}Quick setup:${NC}"
echo -e "  1. Run database migrations:"
echo -e "     ${CYAN}psql -h localhost -U postgres < ./selfhost/supabase/migrations/001_profiles.sql${NC}"
echo -e "  2. Check logs:"
echo -e "     ${CYAN}./logs-ossp.sh${NC}"
echo -e "  3. Stop services:"
echo -e "     ${CYAN}./stop-ossp.sh${NC}"

echo ""

# Show logs if requested
if [ "$NO_LOGS" = false ]; then
    echo -e "${CYAN}📺 Showing logs (press Ctrl+C to stop)...${NC}"
    docker-compose -f "$SCRIPT_DIR/docker-compose.yml" logs -f
fi
