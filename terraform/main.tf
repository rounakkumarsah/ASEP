terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# =============================================================================
# Variables
# =============================================================================

variable "aws_region" {
  description = "AWS region for the deployment"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 Instance type (t3.xlarge recommended for Neo4j, Qdrant, Postgres + AI workloads)"
  type        = string
  default     = "t3.xlarge" 
}

variable "key_name" {
  description = "Name of an existing EC2 KeyPair to enable SSH access. Leave empty if using Session Manager."
  type        = string
  default     = ""
}

variable "repo_url" {
  description = "URL of the repository to clone"
  type        = string
  default     = "https://github.com/rounakkumarsah/ASEP.git"
}

# =============================================================================
# Data Sources
# =============================================================================

# Fetch the latest Ubuntu 22.04 LTS AMI (Canonical)
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# =============================================================================
# Resources
# =============================================================================

# Security Group for the Enterprise Stack
resource "aws_security_group" "asep_sg" {
  name        = "asep-enterprise-sg"
  description = "Allow inbound web traffic and SSH. Internal ports remain closed to the public."

  # SSH access (Restrict CIDR in production)
  ingress {
    description = "SSH Access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP for web traffic
  ingress {
    description = "HTTP Web Traffic"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS for secure web traffic
  ingress {
    description = "HTTPS Web Traffic"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Note: Internal ports like 5432 (Postgres), 6379 (Redis), 7687 (Neo4j), 
  # 6333 (Qdrant), 3000 (Next.js), and 8000 (FastAPI) are deliberately NOT 
  # opened in this SG. They communicate securely over the internal Docker network.

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "asep-enterprise-sg"
  }
}

# High-Performance EC2 Instance
resource "aws_instance" "asep_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  key_name      = var.key_name != "" ? var.key_name : null

  vpc_security_group_ids = [aws_security_group.asep_sg.id]

  # Provision sufficient storage for Vector DBs, Graph DBs, and Docker images
  root_block_device {
    volume_size = 100
    volume_type = "gp3"
    iops        = 3000
    throughput  = 125
  }

  # user_data script executes as root on first boot
  user_data = <<-EOF
    #!/bin/bash
    set -e
    # Log output to console and file for debugging
    exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
    
    echo "=========================================================="
    echo " 1. Updating System..."
    echo "=========================================================="
    apt-get update -y
    apt-get upgrade -y
    apt-get install -y ca-certificates curl gnupg git openssl jq
    
    echo "=========================================================="
    echo " 2. Installing Docker & Docker Compose..."
    echo "=========================================================="
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Add default ubuntu user to docker group
    usermod -aG docker ubuntu

    echo "=========================================================="
    echo " 3. Cloning Repository..."
    echo "=========================================================="
    mkdir -p /opt/asep
    cd /opt/asep
    git clone ${var.repo_url} .

    echo "=========================================================="
    echo " 4. Configuring Environment Variables (.env)..."
    echo "=========================================================="
    # Fetch instance public IP dynamically from AWS metadata service (IMDSv2)
    TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
    PUBLIC_IP=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-ipv4)

    # Generate cryptographically secure passwords and secrets
    POSTGRES_PASSWORD=$(openssl rand -hex 16)
    REDIS_PASSWORD=$(openssl rand -hex 16)
    NEO4J_PASSWORD=$(openssl rand -hex 16)
    JWT_SECRET=$(openssl rand -hex 32)
    SECRET_KEY=$(openssl rand -hex 32)

    cat <<ENV_EOF > .env
APP_ENV=production
DOMAIN=$${PUBLIC_IP}

# Security
SECRET_KEY=$${SECRET_KEY}
JWT_SECRET_KEY=$${JWT_SECRET}
JWT_REFRESH_SECRET_KEY=$(openssl rand -hex 32)

# Databases
DATABASE_URL=postgresql+asyncpg://asep_user:$${POSTGRES_PASSWORD}@postgres:5432/asep_db
REDIS_URL=redis://:$${REDIS_PASSWORD}@redis:6379/0
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=$${NEO4J_PASSWORD}
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=

# Internal DB Config
POSTGRES_USER=asep_user
POSTGRES_PASSWORD=$${POSTGRES_PASSWORD}
POSTGRES_DB=asep_db
REDIS_PASSWORD=$${REDIS_PASSWORD}

# Networking & URLs
CORS_ORIGINS=http://$${PUBLIC_IP},http://localhost,http://localhost:3000
FRONTEND_URL=http://$${PUBLIC_IP}
PORT=8000
ENV_EOF

    echo "=========================================================="
    echo " 5. Deploying Multi-Container Stack..."
    echo "=========================================================="
    # Use docker-compose.prod.yml if it exists, fallback to standard docker-compose.yml
    if [ -f "docker-compose.prod.yml" ]; then
      COMPOSE_FILE="docker-compose.prod.yml"
    else
      COMPOSE_FILE="docker-compose.yml"
    fi

    docker compose -f $COMPOSE_FILE up -d --build

    echo "Deployment completed successfully."
  EOF

  tags = {
    Name = "ASEP-Enterprise-Production-Node"
  }
}

# =============================================================================
# Outputs
# =============================================================================

output "public_ip" {
  description = "Public IP address of the deployed EC2 instance"
  value       = aws_instance.asep_server.public_ip
}

output "application_url" {
  description = "Direct HTTP URL to access the platform (Wait ~3-5 mins for initial boot)"
  value       = "http://${aws_instance.asep_server.public_ip}"
}
