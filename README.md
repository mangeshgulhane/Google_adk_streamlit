# Google_adk_streamlit
This AI agents demonstrate streamlit App integration
Google ADK Persona 

# deployment
## creating Artifact registry
### gcloud artifacts repositories create "ai-agent-repo" --location="us-central1" --repository-format=Docker

## submitting docker build 
$VERSION = git rev-parse --short HEAD
$GOOGLE_CLOUD_REGION = "us-central1"
$GOOGLE_CLOUD_PROJECT= "agentic-ai-solution"
$REPO = "ai-agent-repo"
$SERVICE_NAME = "agentic-chatbot"

## Creating Artifact registry
# One time setup - create a GAR repo
gcloud artifacts repositories create "$REPO" \
  --location="$GOOGLE_CLOUD_REGION" --repository-format=Docker
### o/p:  
us-central1-docker.pkg.dev/agentic-ai-solution/ai-agent-repo

## Allow authentication to the repo
gcloud auth configure-docker "$GOOGLE_CLOUD_REGION-docker.pkg.dev"

## Do this EVERY TIME we want to build a new version and push to GAR
# This will take a minute
export VERSION=$(git rev-parse --short HEAD)

gcloud builds submit \
  --tag "$GOOGLE_CLOUD_REGION-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/$REPO/$SERVICE_NAME:$VERSION"