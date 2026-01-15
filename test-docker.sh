#!/bin/bash
# Quick test script for Docker setup

echo "🐳 Testing Docker Setup..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Test backend Dockerfile
echo "📦 Testing backend Dockerfile..."
cd backend
if [ -f "Dockerfile" ]; then
    echo "✅ backend/Dockerfile found"
else
    echo "❌ backend/Dockerfile not found"
    exit 1
fi
cd ..

# Test frontend Dockerfile
echo "📦 Testing frontend Dockerfile..."
cd frontend
if [ -f "Dockerfile" ]; then
    echo "✅ frontend/Dockerfile found"
else
    echo "❌ frontend/Dockerfile not found"
    exit 1
fi
cd ..

# Test docker-compose
echo "📦 Testing docker-compose.yml..."
if [ -f "docker-compose.yml" ]; then
    echo "✅ docker-compose.yml found"
else
    echo "❌ docker-compose.yml not found"
    exit 1
fi

echo ""
echo "🎉 All Docker files are in place!"
echo ""
echo "Next steps:"
echo "1. Build and run: docker-compose up --build"
echo "2. Access frontend: http://localhost:3000"
echo "3. Access backend: http://localhost:8000"
echo ""
