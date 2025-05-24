# Makefile for managing Railway bot environments

.PHONY: dev prod migrate

dev:
	echo "🚀 Deploying to DEV..."
	railway environment development && railway up

prod:
	echo "🚀 Deploying to PRODUCTION..."
	railway environment production && railway up

migrate:
	./migrate_db.sh

logs-dev:
	railway environment development && railway logs

logs-prod:
	railway environment production && railway logs