#!/bin/bash
# Run all three SABER dashboard applications in parallel
# Each runs on a different port

echo "========================================"
echo "Starting SABER Dashboard Applications"
echo "========================================"
echo ""
echo "App 1: Basic Dashboard      - http://127.0.0.1:8051/"
echo "App 2: Government Analytics - http://127.0.0.1:8052/"
echo "App 3: Temporal Analysis    - http://127.0.0.1:8053/"
echo ""
echo "Press Ctrl+C to stop all apps"
echo "========================================"
echo ""

# Start all three apps in background
python app.py &
APP1_PID=$!

sleep 2
python app_enhanced.py &
APP2_PID=$!

sleep 2
python app_temporal.py &
APP3_PID=$!

echo ""
echo "All apps started!"
echo "PIDs: $APP1_PID, $APP2_PID, $APP3_PID"
echo ""
echo "Press Ctrl+C to stop all apps..."

# Trap Ctrl+C to kill all processes
trap "kill $APP1_PID $APP2_PID $APP3_PID 2>/dev/null; exit" INT

# Wait for any app to finish
wait
