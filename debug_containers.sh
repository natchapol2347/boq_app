#!/bin/bash
# Debug script to check container status and logs

echo "🔍 BOQ Processor - Container Debug Tool"
echo "======================================"

# Check if containers are running
echo "📊 Container Status:"
docker compose ps

echo ""
echo "🔗 Port Status:"
echo "Backend (5000):"
curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/config/inquiry || echo "Not responding"

echo ""
echo "Frontend (8501):"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8501 || echo "Not responding"

echo ""
echo "Admin (8502):"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8502 || echo "Not responding"

echo ""
echo "📋 Recent Logs (last 20 lines each):"
echo "===================================="

echo ""
echo "🖥️  BACKEND LOGS:"
echo "-----------------"
docker compose logs --tail=20 boq-backend

echo ""
echo "🌐 FRONTEND LOGS:"
echo "----------------"
docker compose logs --tail=20 boq-frontend

echo ""
echo "⚙️  ADMIN LOGS:"
echo "--------------"
docker compose logs --tail=20 boq-admin

echo ""
echo "🚨 Error Analysis:"
echo "=================="

# Check for specific errors
echo "Checking for recursion errors..."
if docker compose logs boq-frontend 2>&1 | grep -q "maximum recursion depth exceeded"; then
    echo "❌ FRONTEND has recursion error"
fi

if docker compose logs boq-admin 2>&1 | grep -q "maximum recursion depth exceeded"; then
    echo "❌ ADMIN has recursion error"
fi

# Check for import errors
echo "Checking for import errors..."
if docker compose logs boq-frontend 2>&1 | grep -q "ImportError\|ModuleNotFoundError"; then
    echo "❌ FRONTEND has import error"
fi

if docker compose logs boq-admin 2>&1 | grep -q "ImportError\|ModuleNotFoundError"; then
    echo "❌ ADMIN has import error"
fi

# Check for Streamlit errors
echo "Checking for Streamlit errors..."
if docker compose logs boq-frontend 2>&1 | grep -q "set_page_config"; then
    echo "⚠️  FRONTEND has set_page_config issue"
fi

if docker compose logs boq-admin 2>&1 | grep -q "set_page_config"; then
    echo "⚠️  ADMIN has set_page_config issue"
fi

echo ""
echo "💡 Troubleshooting Tips:"
echo "======================="
echo "1. If recursion error: Check st.set_page_config() protection"
echo "2. If import error: Check file paths and dependencies"  
echo "3. If set_page_config error: Ensure it's called only once"
echo "4. To restart a specific service: docker compose restart [service-name]"
echo "5. To rebuild everything: ./manage.sh rebuild"

echo ""
echo "🔧 Quick Fixes:"
echo "==============="
echo "Restart frontend only: docker compose restart boq-frontend"
echo "Restart admin only:    docker compose restart boq-admin"
echo "View live logs:        docker compose logs -f [service-name]"
echo "Shell into container:  docker compose exec [service-name] /bin/bash"