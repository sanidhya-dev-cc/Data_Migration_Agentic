#!/bin/bash
# Startup script to initialize Oracle databases
# This runs every time the container starts

echo "=========================================="
echo "Oracle Migration POC - Startup Script"
echo "=========================================="

# Wait for database to be ready
echo "Waiting for database to be fully started..."
sleep 30

# Check if initialization has already been done
if [ -f /opt/oracle/oradata/.initialized ]; then
  echo "Database already initialized. Skipping setup."
  exit 0
fi

echo "Running initialization scripts..."

# Run setup scripts
for script in /opt/oracle/scripts/setup/*.sql; do
  if [ -f "$script" ]; then
    echo "Executing: $(basename $script)"
    sqlplus -s /nolog @"$script"
    if [ $? -eq 0 ]; then
      echo "✓ $(basename $script) completed successfully"
    else
      echo "✗ $(basename $script) failed"
    fi
  fi
done

# Mark as initialized
touch /opt/oracle/oradata/.initialized

echo "=========================================="
echo "Initialization complete!"
echo "=========================================="
