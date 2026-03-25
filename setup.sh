#!/bin/bash
# setup.sh - OW_BC Initial Setup Script

set -e

echo "🚀 Starting OW_BC initial setup..."

# 1. Check for .env file
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  NOTE: .env created. You may want to edit it to change default secrets."
else
    echo "✅ .env file already exists."
fi

# 2. Build and start services
echo "🐳 Building and starting Docker containers..."
docker compose up --build -d

# 3. Wait for Database to be ready
echo "⏳ Waiting for database to be ready..."
until docker compose exec db pg_isready -U owbc > /dev/null 2>&1; do
  echo "   ...waiting for postgres..."
  sleep 2
done

# 4. Run Migrations
echo "🏗️ Running database migrations..."
docker compose exec backend alembic upgrade head || echo "⚠️  Migrations may already be applied or have issues. Continuing..."

echo "✨ Setup complete!"
echo "--------------------------------------------------"
echo "🌐 Frontend:    http://localhost:3000"
echo "📂 API Docs:    http://localhost:8000/docs"
echo "🏥 Health:      http://localhost:8000/healthz"
echo "--------------------------------------------------"
echo "You can now register a new account at the Frontend."
