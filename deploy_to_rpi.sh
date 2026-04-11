#!/bin/bash
# Deploy Traffic Violation Detection to Raspberry Pi

echo "=========================================="
echo "  DEPLOY TO RASPBERRY PI"
echo "=========================================="
echo ""

# Configuration
RPI_USER="pi"
RPI_HOST="raspberrypi.local"
PROJECT_DIR="traffic_violation_detection"

# Check if RPi address is provided
if [ ! -z "$1" ]; then
    RPI_HOST="$1"
fi

echo "Target: $RPI_USER@$RPI_HOST"
echo ""

# Step 1: Package project
echo "📦 Step 1: Packaging project..."
cd ~
tar -czf traffic_violation.tar.gz $PROJECT_DIR \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.md' \
    --exclude='docs'

if [ $? -ne 0 ]; then
    echo "❌ Failed to package project"
    exit 1
fi

echo "✅ Project packaged"
echo ""

# Step 2: Copy to RPi
echo "📤 Step 2: Copying to Raspberry Pi..."
scp traffic_violation.tar.gz $RPI_USER@$RPI_HOST:~

if [ $? -ne 0 ]; then
    echo "❌ Failed to copy to RPi"
    echo "   Check if RPi is accessible: ping $RPI_HOST"
    exit 1
fi

echo "✅ Files copied"
echo ""

# Step 3: Deploy on RPi
echo "🚀 Step 3: Deploying on Raspberry Pi..."

ssh $RPI_USER@$RPI_HOST << 'EOF'
    echo "Extracting files..."
    tar -xzf traffic_violation.tar.gz
    cd traffic_violation_detection
    
    echo "Installing dependencies..."
    pip install -r backend_requirements.txt
    
    echo "Installing RPi camera support..."
    pip install picamera2
    
    echo "✅ Deployment complete!"
    echo ""
    echo "To start the system:"
    echo "  cd traffic_violation_detection"
    echo "  python backend/run_server.py --host 0.0.0.0 --port 8000"
EOF

if [ $? -ne 0 ]; then
    echo "❌ Deployment failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "  ✅ DEPLOYMENT SUCCESSFUL"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. SSH into RPi: ssh $RPI_USER@$RPI_HOST"
echo "  2. Start system: cd $PROJECT_DIR && python backend/run_server.py"
echo "  3. Access API: http://$RPI_HOST:8000/docs"
echo ""
