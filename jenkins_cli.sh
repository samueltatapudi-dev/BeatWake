#!/bin/bash

# Jenkins CLI Helper Script for BeatWake
# Provides easy commands to interact with Jenkins

JENKINS_URL="http://localhost:8080"
JOB_NAME="BeatWake-Pipeline"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function show_help {
    cat << EOF
🔧 Jenkins CLI Helper for BeatWake

Usage: ./jenkins_cli.sh [command]

Commands:
    status          - Check Jenkins status
    build           - Trigger a new build
    logs            - View latest build logs
    list            - List recent builds
    artifacts       - Download latest artifacts
    url             - Get Jenkins and job URLs
    restart         - Restart Jenkins service
    password        - Show initial admin password
    help            - Show this help message

Examples:
    ./jenkins_cli.sh build
    ./jenkins_cli.sh logs
    ./jenkins_cli.sh status

EOF
}

function check_jenkins {
    if ! sudo systemctl is-active --quiet jenkins; then
        echo -e "${RED}❌ Jenkins is not running${NC}"
        echo "Start with: sudo systemctl start jenkins"
        exit 1
    fi
}

function jenkins_status {
    echo -e "${YELLOW}📊 Checking Jenkins status...${NC}"
    echo ""
    sudo systemctl status jenkins --no-pager | head -20
    echo ""
    echo -e "${GREEN}✅ Jenkins is running${NC}"
    echo "URL: $JENKINS_URL"
}

function trigger_build {
    check_jenkins
    echo -e "${YELLOW}🚀 Triggering build for $JOB_NAME...${NC}"
    
    # Try with curl
    response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$JENKINS_URL/job/$JOB_NAME/build")
    
    if [ "$response" = "201" ] || [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ Build triggered successfully!${NC}"
        echo "View at: $JENKINS_URL/job/$JOB_NAME"
    else
        echo -e "${RED}❌ Failed to trigger build (HTTP $response)${NC}"
        echo "Try: $JENKINS_URL/job/$JOB_NAME/build?delay=0sec"
    fi
}

function view_logs {
    check_jenkins
    echo -e "${YELLOW}📋 Fetching latest build logs...${NC}"
    echo ""
    
    curl -s "$JENKINS_URL/job/$JOB_NAME/lastBuild/consoleText" || \
        echo -e "${RED}❌ Could not fetch logs. Build may not exist yet.${NC}"
}

function list_builds {
    check_jenkins
    echo -e "${YELLOW}📝 Recent builds:${NC}"
    echo ""
    
    # Get build info
    builds=$(curl -s "$JENKINS_URL/job/$JOB_NAME/api/json" | \
             python3 -c "import sys, json; data=json.load(sys.stdin); \
             [print(f\"#{b['number']}: {b['result'] or 'RUNNING'}\") for b in data.get('builds', [])[:5]]" 2>/dev/null)
    
    if [ -n "$builds" ]; then
        echo "$builds"
    else
        echo "No builds found or job doesn't exist yet"
    fi
    
    echo ""
    echo "View all: $JENKINS_URL/job/$JOB_NAME"
}

function download_artifacts {
    check_jenkins
    echo -e "${YELLOW}📦 Downloading latest artifacts...${NC}"
    
    artifact_url="$JENKINS_URL/job/$JOB_NAME/lastSuccessfulBuild/artifact/dist/"
    
    echo "Artifacts available at: $artifact_url"
    echo ""
    echo "Download with:"
    echo "  curl -O ${artifact_url}BeatWake-*.tar.gz"
}

function show_urls {
    echo -e "${GREEN}🌐 Jenkins URLs:${NC}"
    echo ""
    echo "Dashboard:        $JENKINS_URL"
    echo "Job:              $JENKINS_URL/job/$JOB_NAME"
    echo "Last Build:       $JENKINS_URL/job/$JOB_NAME/lastBuild"
    echo "Blue Ocean:       $JENKINS_URL/blue/organizations/jenkins/$JOB_NAME"
    echo "Credentials:      $JENKINS_URL/credentials"
    echo ""
}

function restart_jenkins {
    echo -e "${YELLOW}🔄 Restarting Jenkins...${NC}"
    sudo systemctl restart jenkins
    echo -e "${GREEN}✅ Jenkins restarted${NC}"
    echo "Wait 30 seconds for initialization..."
    sleep 5
}

function show_password {
    if [ -f /var/lib/jenkins/secrets/initialAdminPassword ]; then
        echo -e "${YELLOW}🔑 Initial Admin Password:${NC}"
        echo ""
        sudo cat /var/lib/jenkins/secrets/initialAdminPassword
        echo ""
    else
        echo -e "${RED}❌ Password file not found. Jenkins may already be configured.${NC}"
    fi
}

# Main script
case "${1:-help}" in
    status)
        jenkins_status
        ;;
    build)
        trigger_build
        ;;
    logs)
        view_logs
        ;;
    list)
        list_builds
        ;;
    artifacts)
        download_artifacts
        ;;
    url)
        show_urls
        ;;
    restart)
        restart_jenkins
        ;;
    password)
        show_password
        ;;
    help|*)
        show_help
        ;;
esac
