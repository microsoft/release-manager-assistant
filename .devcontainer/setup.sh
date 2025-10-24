#!/bin/bash

# Update git repository
git fetch
git pull

# Copy environment templates
echo "Setting up environment files..."
if [ ! -f .env ]; then
    cp .env.template .env
    echo "Created .env from template. Please configure your environment variables."
fi

# Install Python dependencies
echo "Installing Python dependencies..."
cd src
python -m pip install --upgrade pip
pip install wheel

# Build and install common package
cd backend/common
python setup.py bdist_wheel
pip install --force-reinstall ./dist/common-0.1.0-py3-none-any.whl
cd ../..

# Install backend service dependencies
echo "Installing backend dependencies..."
cd backend/services/session_manager
pip install -r requirements.txt
cd ../orchestrator
pip install -r requirements.txt
cd ../../mcp_server
pip install -r requirements.txt
cd ../../

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend/react-app
npm install
cd ../../

echo "Development environment setup complete!"
echo ""
echo "To start the full application stack:"
echo "  docker-compose up"
echo ""
echo "Or start individual services:"
echo "  - Frontend: cd src/frontend/react-app && npm run dev"
echo "  - Session Manager: cd src/backend/services/session_manager && python app.py"
echo "  - Orchestrator: cd src/backend/services/orchestrator && python app.py"
echo "  - Redis: docker run -p 6379:6379 redis:7-alpine"
echo ""
echo "Available services:"
echo "  - Frontend: http://localhost:3000"
echo "  - Session Manager: http://localhost:5000"
echo "  - Orchestrator: http://localhost:5002"
echo "  - Redis: localhost:6379"