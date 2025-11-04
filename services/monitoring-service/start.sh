#!/bin/bash

echo "🚀 Starting SADAE Monitoring Service..."

# Start the FastAPI application in the background
echo "📡 Starting monitoring service on port 8002..."
uvicorn main:app --host 0.0.0.0 --port 8002 &

# Store the PID of the main application
MAIN_PID=$!

# Wait for the service to be ready
echo "⏳ Waiting for service to be ready..."
sleep 10

# Check if main service is still running
if kill -0 $MAIN_PID 2>/dev/null; then
    echo "✅ Monitoring service started successfully"
    
    # Start the sensor simulator
    echo "🔧 Starting sensor simulator..."
    python sensor_simulator.py &
    SIMULATOR_PID=$!
    
    echo "✅ Sensor simulator started"
else
    echo "❌ Failed to start monitoring service"
    exit 1
fi

# Function to handle shutdown
cleanup() {
    echo "🛑 Shutting down services..."
    kill $MAIN_PID 2>/dev/null
    kill $SIMULATOR_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Wait for all background processes
wait