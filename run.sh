#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment (venv) not found. Please run ./setup.sh first.${NC}"
    exit 1
fi

# Activate Virtual Environment
source venv/bin/activate

# Function to show usage
show_help() {
    echo "Usage: ./run.sh [options]"
    echo ""
    echo "Options:"
    echo "  --all                Run BOTH Backend API and Frontend Dashboard"
    echo "  --symbol [SYMBOL]    Analyze a specific symbol (e.g., VNM, FPT)"
    echo "  --dry-run            Run without sending notifications"
    echo "  --frontend           Run ONLY the Next.js frontend dashboard"
    echo "  --api                Run ONLY the FastAPI backend server"
    echo "  --dashboard          Run the legacy Streamlit dashboard"
    echo "  --help               Show this help message"
    echo ""
    echo "Example:"
    echo "  ./run.sh --all"
}

# Handle options
if [ "$#" -eq 0 ]; then
    show_help
    exit 0
fi

case "$1" in
    --all)
        echo -e "${BLUE}🚀 Starting Full Stack (Backend + Frontend)...${NC}"
        
        # Cleanup function to kill background processes on exit
        cleanup() {
            echo -e "\n${RED}🛑 Stopping all services...${NC}"
            kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
            exit
        }
        trap cleanup SIGINT

        # Start Backend
        echo -e "${BLUE}🌐 Starting Backend API...${NC}"
        uvicorn api.main:app --reload --port 8000 &
        BACKEND_PID=$!

        # Start Frontend
        echo -e "${BLUE}⚛️ Starting Frontend Dashboard...${NC}"
        cd frontend && npm run dev &
        FRONTEND_PID=$!
        
        echo -e "${GREEN}✅ Both services are running.${NC}"
        echo -e "${BLUE}🔗 API: http://localhost:8000${NC}"
        echo -e "${BLUE}🔗 Frontend: http://localhost:3000${NC}"
        echo -e "${BLUE}Press Ctrl+C to stop both.${NC}"
        
        # Wait for processes
        wait
        ;;
    --frontend)
        echo -e "${BLUE}⚛️ Starting Next.js Frontend Dashboard...${NC}"
        cd frontend && npm run dev
        ;;
    --dashboard)
        echo -e "${BLUE}🖥️ Starting Streamlit Dashboard...${NC}"
        streamlit run app.py
        ;;
    --api)
        echo -e "${BLUE}🌐 Starting API Server...${NC}"
        uvicorn api.main:app --reload --port 8000
        ;;
    --help)
        show_help
        ;;
    *)
        echo -e "${BLUE}📊 Running Analysis with arguments: $@${NC}"
        python main.py "$@"
        ;;
esac



