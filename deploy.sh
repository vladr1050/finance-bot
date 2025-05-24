#!/bin/bash

ENV=$1

if [[ "$ENV" != "dev" && "$ENV" != "production" ]]; then
  echo "❌ Usage: ./deploy.sh [dev|production]"
  exit 1
fi

echo "🚀 Deploying to Railway environment: $ENV"

# Select the environment in Railway CLI
railway environment $ENV

# Deploy the current state to selected environment
railway up

echo "✅ Deployment to $ENV completed."