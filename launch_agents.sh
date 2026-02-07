#!/bin/bash
#
# Launch all Claims Adjudication agents
# Usage: ./launch_agents.sh [all|medical|fraud|policy|cost|orchestrator]
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to launch an agent in the background
launch_agent() {
    local agent_name=$1
    local agent_file=$2
    local log_file="logs/${agent_name}.log"

    echo -e "${BLUE}🚀 Launching ${agent_name}...${NC}"
    mkdir -p logs
    python "agents/${agent_file}" > "$log_file" 2>&1 &
    local pid=$!
    echo "$pid" > "logs/${agent_name}.pid"
    echo -e "${GREEN}✅ ${agent_name} started (PID: $pid)${NC}"
    echo "   Log: $log_file"
}

# Function to stop all agents
stop_agents() {
    echo -e "${YELLOW}🛑 Stopping all agents...${NC}"
    for pid_file in logs/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            agent_name=$(basename "$pid_file" .pid)
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid"
                echo -e "${GREEN}✅ Stopped ${agent_name} (PID: $pid)${NC}"
            fi
            rm "$pid_file"
        fi
    done
}

# Function to check agent status
check_status() {
    echo -e "${BLUE}📊 Agent Status:${NC}"
    echo "-----------------------------------"
    for pid_file in logs/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            agent_name=$(basename "$pid_file" .pid)
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${GREEN}✅ ${agent_name}: RUNNING (PID: $pid)${NC}"
            else
                echo -e "${RED}❌ ${agent_name}: STOPPED${NC}"
                rm "$pid_file"
            fi
        fi
    done
}

# Main script logic
case "${1:-all}" in
    all)
        echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${BLUE}   CLAIMS ADJUDICATION MULTI-AGENT SYSTEM${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
        echo ""

        # Check if AgentField server is running
        if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
            echo -e "${RED}❌ ERROR: AgentField server is not running!${NC}"
            echo -e "${YELLOW}Please start it first: af server${NC}"
            exit 1
        fi

        echo -e "${GREEN}✅ AgentField server is running${NC}"
        echo ""
        echo "Launching all agents..."
        echo ""

        launch_agent "medical-reasoner" "medical_agent.py"
        sleep 2
        launch_agent "fraud-detector" "fraud_agent.py"
        sleep 2
        launch_agent "policy-checker" "policy_agent.py"
        sleep 2
        launch_agent "cost-analyzer" "cost_agent.py"
        sleep 2
        launch_agent "orchestrator" "orchestrator_agent.py"

        echo ""
        echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}✅ All agents launched successfully!${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "Logs are in the 'logs/' directory"
        echo ""
        echo "Test the system:"
        echo -e "${YELLOW}curl -X POST http://localhost:8080/api/v1/execute/claims-orchestrator.adjudicate_claim \\${NC}"
        echo -e "${YELLOW}  -H 'Content-Type: application/json' \\${NC}"
        echo -e "${YELLOW}  -d '{\"input\": {\"claim_id\": \"CLM10001\"}}'${NC}"
        echo ""
        echo "To stop all agents: ./launch_agents.sh stop"
        echo "To check status: ./launch_agents.sh status"
        ;;

    medical)
        launch_agent "medical-reasoner" "medical_agent.py"
        ;;

    fraud)
        launch_agent "fraud-detector" "fraud_agent.py"
        ;;

    policy)
        launch_agent "policy-checker" "policy_agent.py"
        ;;

    cost)
        launch_agent "cost-analyzer" "cost_agent.py"
        ;;

    orchestrator)
        launch_agent "orchestrator" "orchestrator_agent.py"
        ;;

    stop)
        stop_agents
        ;;

    status)
        check_status
        ;;

    *)
        echo "Usage: $0 [all|medical|fraud|policy|cost|orchestrator|stop|status]"
        echo ""
        echo "Commands:"
        echo "  all           - Launch all agents (default)"
        echo "  medical       - Launch only medical reasoner"
        echo "  fraud         - Launch only fraud detector"
        echo "  policy        - Launch only policy checker"
        echo "  cost          - Launch only cost analyzer"
        echo "  orchestrator  - Launch only orchestrator"
        echo "  stop          - Stop all running agents"
        echo "  status        - Check agent status"
        exit 1
        ;;
esac
