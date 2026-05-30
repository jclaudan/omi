#!/bin/bash
set -euo pipefail

# ============================================
# View Omi OSS+ Logs (Linux/macOS)
# ============================================
# Usage: ./logs-ossp.sh [OPTIONS]
# Options:
#   -s, --service   Service name (supabase, qdrant, minio, faster-whisper, ollama, redis)
#   -n, --lines     Number of lines to show (default: 100)
#   -f, --follow    Follow log output (like 'tail -f')
#   --help          Show this message

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE=""
LINES=100
FOLLOW=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        -n|--lines)
            LINES="$2"
            shift 2
            ;;
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        --help)
            cat << 'EOF'
View Omi OSS+ Service Logs

Usage: ./logs-ossp.sh [OPTIONS]

Options:
  -s, --service SERVICE   Service name (supabase, qdrant, minio, faster-whisper, ollama, redis)
  -n, --lines N           Number of lines to show (default: 100)
  -f, --follow            Follow log output (like 'tail -f')
  --help                  Show this message

Examples:
  ./logs-ossp.sh                                 # Show all logs
  ./logs-ossp.sh -s supabase                     # Show Supabase logs
  ./logs-ossp.sh -s ollama -f                    # Follow Ollama logs
  ./logs-ossp.sh -s faster-whisper -n 50        # Show last 50 Faster-Whisper logs
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
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Map service names to container names
declare -A SERVICE_MAP=(
    ["supabase"]="omi-supabase"
    ["qdrant"]="omi-qdrant"
    ["minio"]="omi-minio"
    ["faster-whisper"]="omi-faster-whisper"
    ["whisper"]="omi-faster-whisper"
    ["ollama"]="omi-ollama"
    ["redis"]="omi-redis"
)

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    exit 1
fi

# Build command
CMD=("docker-compose" "-f" "$SCRIPT_DIR/docker-compose.yml" "logs")

if [ -n "$SERVICE" ]; then
    # Find matching service
    CONTAINER=""
    for key in "${!SERVICE_MAP[@]}"; do
        if [[ "$key" == "$SERVICE"* ]]; then
            CONTAINER="${SERVICE_MAP[$key]}"
            break
        fi
    done

    if [ -z "$CONTAINER" ]; then
        echo -e "${RED}❌ Unknown service: $SERVICE${NC}"
        echo -e "${YELLOW}Available services:${NC}"
        for key in "${!SERVICE_MAP[@]}"; do
            echo -e "  - $key"
        done
        exit 1
    fi

    echo -e "${CYAN}📺 Logs for $CONTAINER${NC}"
    CMD+=("$CONTAINER")
else
    echo -e "${CYAN}📺 Logs for all services (press Ctrl+C to exit)${NC}"
fi

# Add options
if [ "$FOLLOW" = true ]; then
    CMD+=("-f")
else
    CMD+=("--tail=$LINES")
fi

# Add timestamp
CMD+=("-t")

# Execute
"${CMD[@]}"
