#!/bin/bash

# Path to the locally installed gcloud CLI
GCLOUD="/home/hafsajavedpak/Projects/ciro/google-cloud-sdk/bin/gcloud"

echo "======================================"
echo "    GCP Backend Deployment Script     "
echo "======================================"
echo ""

echo "[1/4] Checking gcloud CLI installation..."
if [ ! -f "$GCLOUD" ]; then
    echo "Error: gcloud CLI not found at $GCLOUD."
    exit 1
fi

echo "[2/4] Checking Google Cloud authentication..."
# Check if the user is authenticated with a personal account rather than a service account
ACCOUNT=$($GCLOUD config get-value core/account 2>/dev/null)

if [[ "$ACCOUNT" == *"gserviceaccount.com"* ]] || [[ -z "$ACCOUNT" ]]; then
    echo "You are currently authenticated as a service account or not logged in."
    echo "To deploy to Cloud Run, you must log in with your personal Google account."
    echo "Opening login prompt..."
    $GCLOUD auth login
else
    echo "Authenticated as $ACCOUNT"
fi

echo "[3/4] Setting project and enabling APIs..."
$GCLOUD config set project emerald-energy-483903-f3
$GCLOUD services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

echo "[4/4] Building and deploying backend to Google Cloud Run..."
# Navigate to the backend directory where the Dockerfile is located
cd /home/hafsajavedpak/Projects/ciro/backend

$GCLOUD run deploy ciro-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="OPENWEATHER_API_KEY=\${OPENWEATHER_API_KEY},FIREBASE_PROJECT_ID=ciro-61389,GOOGLE_APPLICATION_CREDENTIALS=backend/firebase-credentials.json,ENVIRONMENT=production,DEMO_CITY_LAT=33.6844,DEMO_CITY_LNG=73.0479,DEMO_CITY_NAME=Islamabad,GEMINI_API_KEY=\${GEMINI_API_KEY}"

echo ""
echo "======================================"
echo "        Deployment Complete!          "
echo "======================================"
echo "Copy the 'Service URL' from the output above and use it in your Flutter app."
