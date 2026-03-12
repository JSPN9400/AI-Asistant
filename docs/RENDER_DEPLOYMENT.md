# Render Deployment

This repo can be deployed to Render as a single web service for demo and testing.

## What Render Can Host Here

- `API`: yes
- `web app`: yes
- `APK`: not as a running app

Render web services are for dynamic applications such as FastAPI apps, and Render static sites are for frontend hosting. Source:

- https://render.com/docs/web-services
- https://render.com/docs/static-sites

## Important Limitation

Render services use an ephemeral filesystem by default. That means local SQLite data and uploaded files can be lost after a restart or redeploy unless you use a persistent disk, and persistent disks are for paid services. Source:

- https://render.com/docs/disks

For checking and demo purposes, this is acceptable. For stable data, move to Postgres and object storage.

## Deploy From GitHub

### 1. Push this repo to GitHub

Make sure the repository contains:

- [render.yaml](/e:/My%20project%20with%20git/AI-Asistant/render.yaml)

### 2. Create the Render service

In Render:

1. Click `New +`
2. Click `Blueprint`
3. Connect your GitHub repo
4. Select this repository
5. Render will detect `render.yaml`
6. Click `Apply`

Render Blueprints are defined by a root `render.yaml` file. Source:

- https://render.com/docs/blueprint-spec

### 3. Wait for deploy

Render will:

- install Python dependencies from `backend/requirements.txt`
- start the FastAPI app
- expose it on your Render URL

### 4. Open the app

After deploy, use:

- `https://<your-service>.onrender.com/`
- `https://<your-service>.onrender.com/docs`
- `https://<your-service>.onrender.com/health`

## Demo Login

- email: `demo@company.com`
- password: `demo-pass`
- workspace: `demo-workspace`

## APK Guidance

Render does not run Android APKs as applications.

Use this split:

- `API`: Render web service
- `web app`: same Render web service in this repo
- `APK`: distribute separately

Recommended APK distribution options:

- GitHub Releases
- Firebase App Distribution
- Google Play internal testing

If you only want to host the APK file for download, a static file host can do that, but that is not the same as hosting the Android app runtime.
