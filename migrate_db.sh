#!/bin/bash

# Export from production
echo "📤 Exporting production DB..."
pg_dump postgresql://postgres:cHNOuDBDHEsGFMttGwfXQMkvlGGWMNNy@trolley.proxy.rlwy.net:35668/railway > production_backup.sql

# Import into dev
echo "📥 Importing into dev DB..."
psql postgresql://postgres:txXfTvsGhrWsTJhRsyjWTSRdxPJrXMvg@mainline.proxy.rlwy.net:17014/railway < production_backup.sql

echo "✅ Migration completed from production to dev."