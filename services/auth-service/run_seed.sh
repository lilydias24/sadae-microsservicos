#!/bin/bash

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 10

# Run seed data script
echo "Creating initial users..."
python seed_data.py

echo "Seed data creation completed!"
