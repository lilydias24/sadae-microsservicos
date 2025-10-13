#!/bin/bash

# Start the FastAPI application in the background
uvicorn main:app --host 0.0.0.0 --port 8002 &

# Wait for the service to be ready
sleep 5

# Start the sensor simulator
python sensor_simulator.py &

# Wait for all background processes
wait

