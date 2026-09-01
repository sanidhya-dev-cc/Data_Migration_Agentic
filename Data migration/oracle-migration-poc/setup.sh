#!/bin/bash

# Oracle Migration POC - Setup Script
# This script sets up the development environment

echo "=========================================="
echo "Oracle Migration POC - Setup"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your Azure OpenAI credentials"
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✓ Docker and Docker Compose are installed"
echo ""

# Create logs directory
echo "Creating logs directory..."
mkdir -p logs
echo "✓ Logs directory created"
echo ""

# Build and start containers
echo "Building Docker containers..."
docker-compose build

echo ""
echo "Starting containers..."
docker-compose up -d

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Services:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""
echo "⚠️  Don't forget to configure your Azure OpenAI credentials in .env"
echo ""
