# AWS EC2 Deployment

This project can be deployed on a single EC2 instance for testing.

## What This Deploys

- FastAPI backend
- bundled static web frontend on `/`
- SQLite database stored on the EC2 host through Docker volumes
- file uploads stored on the EC2 host through Docker volumes

## AWS Console Steps

### 1. Launch an EC2 instance

Recommended for a low-cost test deployment:

- AMI: `Ubuntu Server 24.04 LTS`
- Instance type: `t2.micro` or `t3.micro` if your free-tier or credits allow it
- Storage: `16 GB` is enough for testing

### 2. Create or select a security group

Inbound rules:

- `SSH` on port `22` from `My IP`
- `HTTP` on port `80` from `Anywhere`

AWS docs say new security groups start with no inbound rules, so you must explicitly add the ones you need:

- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-rules.html
- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/creating-security-group.html

### 3. Connect to the instance

Use EC2 Instance Connect from the AWS console or SSH from your machine.

AWS docs:

- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Connect-using-EC2-Instance-Connect.html

## Server Setup Commands

Run these on the EC2 instance after connecting.

### 4. Install Docker and Compose

These commands follow Docker's official Ubuntu installation path:

- https://docs.docker.com/engine/install/ubuntu/

```bash
sudo apt update
sudo apt install -y ca-certificates curl git
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

After `usermod`, log out and log back in once.

### 5. Clone your GitHub repo

```bash
git clone <YOUR_GITHUB_REPO_URL>
cd AI-Asistant
```

### 6. Create the EC2 env file

```bash
cp backend/.env.ec2.example backend/.env.ec2
nano backend/.env.ec2
```

Set at least:

```env
APP_ENV=production
ASSISTANT_API_KEY=change-this
JWT_SECRET=change-this-too
ASSISTANT_ENABLE_CLOUD_REASONER=false
```

If you want Gemini later:

```env
ASSISTANT_ENABLE_CLOUD_REASONER=true
ASSISTANT_LLM_PROVIDER=gemini
GEMINI_API_KEY=your_real_key
```

### 7. Build and run the app

```bash
docker compose -f infra/docker/docker-compose.ec2.yml up -d --build
```

### 8. Check the container

```bash
docker compose -f infra/docker/docker-compose.ec2.yml ps
docker compose -f infra/docker/docker-compose.ec2.yml logs -f
```

## Test URLs

Replace `<EC2_PUBLIC_IP>` with your actual instance IP.

- `http://<EC2_PUBLIC_IP>/`
- `http://<EC2_PUBLIC_IP>/health`
- `http://<EC2_PUBLIC_IP>/docs`
- `http://<EC2_PUBLIC_IP>/system/status`

## Demo Login

- email: `demo@company.com`
- password: `demo-pass`
- workspace: `demo-workspace`

## Update Deployment

When you push new code to GitHub:

```bash
cd AI-Asistant
git pull
docker compose -f infra/docker/docker-compose.ec2.yml up -d --build
```

## Stop Deployment

```bash
docker compose -f infra/docker/docker-compose.ec2.yml down
```

## Important Notes

- This is suitable for testing, not full production.
- SQLite on one EC2 instance is fine for evaluation, but for production use PostgreSQL.
- Opening port `80` is enough for a plain HTTP test deployment.
- For a real public deployment, add a domain, reverse proxy, and HTTPS.
