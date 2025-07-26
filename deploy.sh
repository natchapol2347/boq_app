#!/bin/bash
# deploy.sh - One-command deployment

echo "🚀 Deploying BOQ Processor with Docker..."
echo ""

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Get the local IP for user instructions
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || hostname -I | awk '{print $1}' || echo "localhost")

echo "🐳 Building and starting containers..."
docker-compose down  # Stop any existing containers
docker-compose up --build -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "🎉 BOQ Processor is now running!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📱 For users on this network:"
    echo "   🌐 Main App: http://${LOCAL_IP}:8501"
    echo "   🔧 API: http://${LOCAL_IP}:5000"
    echo ""
    echo "📱 For users on this computer:"
    echo "   🌐 Main App: http://localhost:8501"
    echo "   🔧 API: http://localhost:5000"
    echo ""
    echo "👥 EASY USER SETUP:"
    echo "   1. Send users this link: http://${LOCAL_IP}:8501"
    echo "   2. Tell them to bookmark it"
    echo "   3. They use it like any website!"
    echo ""
    echo "🛠️  Management Commands:"
    echo "   • Stop system: docker-compose down"
    echo "   • View logs: docker-compose logs -f"
    echo "   • Restart: docker-compose restart"
    echo "   • Update: git pull && ./deploy.sh"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Try to open browser
    if command -v open >/dev/null 2>&1; then
        echo "🌐 Opening browser..."
        open "http://localhost:8501"
    elif command -v xdg-open >/dev/null 2>&1; then
        echo "🌐 Opening browser..."
        xdg-open "http://localhost:8501"
    fi
    
else
    echo "❌ Something went wrong. Check logs:"
    echo "   docker-compose logs"
fi

---

# stop.sh - Easy stop script
#!/bin/bash
# echo "⏹️  Stopping BOQ Processor..."
# docker-compose down
# echo "✅ BOQ Processor stopped"

---

# update.sh - Easy update script  
#!/bin/bash
# echo "🔄 Updating BOQ Processor..."
# git pull
# docker-compose down
# docker-compose up --build -d
# echo "✅ BOQ Processor updated and restarted"

---

# logs.sh - Easy log viewing
#!/bin/bash
# echo "📋 BOQ Processor Logs (Ctrl+C to exit):"
# docker-compose logs -f