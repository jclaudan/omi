#!/bin/bash
set -euo pipefail

# ============================================
# Stop Omi OSS+ Stack (Linux/macOS)
# ============================================
# Usage: ./stop-ossp.sh [OPTIONS]
# Options:
#   --remove    Remove containers and volumes (deletes data!)
#   --help      Show this message

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REMOVE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --remove)
            REMOVE=true
            shift
            ;;
        --help)
            cat << 'EOF'
Stop Omi OSS+ Stack

Usage: ./stop-ossp.sh [OPTIONS]

Options:
  --remove    Remove containers and volumes (deletes data!)
  --help      Show this message
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

echo -e "${CYAN}🛑 Stopping Omi OSS+ Stack...${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    exit 1
fi

if [ "$REMOVE" = true ]; then
    echo -e "${RED}🗑️  Removing containers and volumes...${NC}"
    echo -e "${RED}⚠️  WARNING: This will delete all data!${NC}"

    read -p "Are you sure? Type 'yes' to confirm: " -r
    if [ "$REPLY" != "yes" ]; then
        echo -e "${YELLOW}Cancelled${NC}"
        exit 0
    fi

    docker-compose -f "$SCRIPT_DIR/docker-compose.yml" down -v
    echo -e "${GREEN}✓ Containers and volumes removed${NC}"
else
    echo -e "${YELLOW}⏹️  Stopping services...${NC}"
    docker-compose -f "$SCRIPT_DIR/docker-compose.yml" down
    echo -e "${GREEN}✓ Services stopped${NC}"
    echo ""
    echo -e "${CYAN}Tip: Use ./stop-ossp.sh --remove to also delete volumes and data${NC}"
fi

echo ""
echo -e "${GREEN}✓ OSS+ Stack stopped${NC}"
