#!/bin/bash

# Claims Adjudication System - Complete Startup Script
# This script provides an interactive menu to start different components

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${CYAN}======================================================================"
    echo -e "  $1"
    echo -e "======================================================================${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠  $1${NC}"
}

print_error() {
    echo -e "${RED}✗  $1${NC}"
}

check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

start_agentfield_server() {
    print_header "Starting AgentField Server (Port 8080)"

    if check_port 8080; then
        print_warning "AgentField server already running on port 8080"
    else
        print_info "Starting AgentField server..."
        agentfield server start &
        sleep 2
        if check_port 8080; then
            print_success "AgentField server started successfully"
            print_info "AgentField UI: ${CYAN}http://localhost:8080${NC}"
        else
            print_error "Failed to start AgentField server"
            exit 1
        fi
    fi
}

start_agents() {
    print_header "Starting All Agent Instances"

    print_info "Launching 5 specialist agents..."
    python launch_all_agents.py &
    AGENTS_PID=$!

    sleep 5
    print_success "All agents launched"
    print_info "Check AgentField UI for registered agents"
}

start_adapter() {
    print_header "Starting AG-UI Adapter Server (Port 8000)"

    if check_port 8000; then
        print_warning "AG-UI adapter already running on port 8000"
    else
        print_info "Starting AG-UI adapter..."
        cd ag-ui-adapter
        python server.py &
        ADAPTER_PID=$!
        cd ..

        sleep 2
        if check_port 8000; then
            print_success "AG-UI adapter started successfully"
            print_info "WebSocket: ${CYAN}ws://localhost:8000/ws/{session_id}${NC}"
        else
            print_error "Failed to start AG-UI adapter"
            exit 1
        fi
    fi
}

start_frontend() {
    print_header "Starting Frontend UI (Port 3000)"

    if check_port 3000; then
        print_warning "Frontend already running on port 3000"
    else
        cd frontend

        # Check if node_modules exists
        if [ ! -d "node_modules" ]; then
            print_info "Installing frontend dependencies..."
            npm install
        fi

        print_info "Starting Next.js development server..."
        npm run dev &
        FRONTEND_PID=$!
        cd ..

        sleep 5
        if check_port 3000; then
            print_success "Frontend UI started successfully"
            print_info "Open browser: ${CYAN}http://localhost:3000${NC}"
        else
            print_error "Failed to start frontend"
            exit 1
        fi
    fi
}

start_all() {
    print_header "🚀 STARTING COMPLETE CLAIMS ADJUDICATION SYSTEM"
    echo ""

    start_agentfield_server
    echo ""

    start_agents
    echo ""

    start_adapter
    echo ""

    start_frontend
    echo ""

    print_header "✅ SYSTEM READY!"
    echo ""
    print_info "All components are running:"
    echo ""
    echo -e "  ${GREEN}1.${NC} AgentField Server:  ${CYAN}http://localhost:8080${NC}"
    echo -e "  ${GREEN}2.${NC} Multi-Agent System: ${GREEN}5 agents running${NC}"
    echo -e "  ${GREEN}3.${NC} AG-UI Adapter:      ${CYAN}http://localhost:8000${NC}"
    echo -e "  ${GREEN}4.${NC} Frontend UI:        ${CYAN}http://localhost:3000${NC}"
    echo ""
    print_warning "Press Ctrl+C to stop all services"
    echo ""

    # Wait for user interrupt
    trap "cleanup" INT TERM
    wait
}

cleanup() {
    echo ""
    print_header "🛑 SHUTTING DOWN SYSTEM"

    print_info "Stopping all services..."

    # Kill all background jobs
    jobs -p | xargs -r kill 2>/dev/null || true

    # Kill specific processes
    pkill -f "launch_all_agents.py" 2>/dev/null || true
    pkill -f "ag-ui-adapter" 2>/dev/null || true
    pkill -f "next dev" 2>/dev/null || true

    print_success "All services stopped"
    exit 0
}

show_menu() {
    clear
    print_header "CLAIMS ADJUDICATION SYSTEM - STARTUP MENU"
    echo ""
    echo "Select what to start:"
    echo ""
    echo "  1) Start Complete System (All 4 components)"
    echo "  2) Start AgentField Server only"
    echo "  3) Start Agents only"
    echo "  4) Start AG-UI Adapter only"
    echo "  5) Start Frontend UI only"
    echo "  6) Check System Status"
    echo "  0) Exit"
    echo ""
    echo -n "Enter your choice: "
}

check_status() {
    print_header "SYSTEM STATUS CHECK"
    echo ""

    # Check AgentField
    if check_port 8080; then
        print_success "AgentField Server: Running (port 8080)"
    else
        print_warning "AgentField Server: Not running"
    fi

    # Check Adapter
    if check_port 8000; then
        print_success "AG-UI Adapter: Running (port 8000)"
    else
        print_warning "AG-UI Adapter: Not running"
    fi

    # Check Frontend
    if check_port 3000; then
        print_success "Frontend UI: Running (port 3000)"
    else
        print_warning "Frontend UI: Not running"
    fi

    # Check agents
    AGENT_COUNT=$(pgrep -f "launch_all_agents.py" | wc -l)
    if [ "$AGENT_COUNT" -gt 0 ]; then
        print_success "Multi-Agent System: Running ($AGENT_COUNT processes)"
    else
        print_warning "Multi-Agent System: Not running"
    fi

    echo ""
    echo "Press Enter to continue..."
    read
}

# Main execution
if [ "$1" == "all" ]; then
    start_all
else
    while true; do
        show_menu
        read choice

        case $choice in
            1)
                start_all
                ;;
            2)
                start_agentfield_server
                echo ""
                echo "Press Enter to continue..."
                read
                ;;
            3)
                start_agents
                echo ""
                echo "Press Enter to continue..."
                read
                ;;
            4)
                start_adapter
                echo ""
                echo "Press Enter to continue..."
                read
                ;;
            5)
                start_frontend
                echo ""
                echo "Press Enter to continue..."
                read
                ;;
            6)
                check_status
                ;;
            0)
                print_info "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid option. Please try again."
                sleep 1
                ;;
        esac
    done
fi
