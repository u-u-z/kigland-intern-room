#!/bin/bash
# Investment Tracker 持续运行服务脚本
# 用法: ./run-tracker-service.sh [start|stop|status|once]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="/tmp/investment-tracker.pid"
LOG_FILE="$WORKSPACE_DIR/research/investment/service.log"

case "$1" in
    start)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "Tracker is already running (PID: $(cat $PID_FILE))"
            exit 1
        fi
        echo "Starting Investment Tracker daemon..."
        nohup python3 "$SCRIPT_DIR/investment-tracker-v2.py" --daemon --interval 60 >> "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo "Tracker started (PID: $!)"
        ;;
    stop)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                echo "Stopping Tracker (PID: $PID)..."
                kill "$PID"
                rm -f "$PID_FILE"
                echo "Tracker stopped"
            else
                echo "Tracker not running"
                rm -f "$PID_FILE"
            fi
        else
            echo "PID file not found"
        fi
        ;;
    status)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "Tracker is running (PID: $(cat $PID_FILE))"
        else
            echo "Tracker is not running"
        fi
        ;;
    once)
        echo "Running tracker once..."
        python3 "$SCRIPT_DIR/investment-tracker-v2.py" --run-once --mock --report
        ;;
    *)
        echo "Usage: $0 [start|stop|status|once]"
        echo ""
        echo "Commands:"
        echo "  start  - Start daemon mode (check every 60 min)"
        echo "  stop   - Stop daemon"
        echo "  status - Check daemon status"
        echo "  once   - Run once and generate report"
        exit 1
        ;;
esac
