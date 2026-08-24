terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
  required_version = ">= 1.0.0"
}

provider "aws" {
  region = var.aws_region
}

# -----------------------------------------------------------------------------
# Networking
# -----------------------------------------------------------------------------
data "aws_vpc" "default" {
  default = true
}

resource "aws_security_group" "asep_sg" {
  name        = "asep-web-sg-${var.environment}"
  description = "Security group for ASEP Docker host"
  vpc_id      = data.aws_vpc.default.id

  # SSH Access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Consider restricting this in production
  }

  # HTTP for Traefik Let's Encrypt challenge and redirects
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS for Application
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound internet access (required for agent LLM calls and package installs)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "asep-sg"
    Environment = var.environment
  }
}

# -----------------------------------------------------------------------------
# Compute
# -----------------------------------------------------------------------------
resource "aws_key_pair" "deployer" {
  key_name   = "asep-deployer-key-${var.environment}"
  public_key = file(var.ssh_public_key_path)
}

# Find latest Ubuntu 22.04 AMI
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

resource "aws_instance" "asep_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  key_name      = aws_key_pair.deployer.key_name

  vpc_security_group_ids = [aws_security_group.asep_sg.id]

  root_block_device {
    volume_size = 100 # 100GB minimum for Docker images + Vector DB + PostgreSQL
    volume_type = "gp3"
  }

  # User data script to install Docker and Docker Compose automatically
  user_data = <<-EOF
              #!/bin/bash
              set -ex

              # Update packages
              apt-get update -y
              apt-get upgrade -y

              # Install dependencies
              apt-get install -y ca-certificates curl gnupg lsb-release git make jq

              # Add Docker's official GPG key
              mkdir -m 0755 -p /etc/apt/keyrings
              curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

              # Set up the repository
              echo \
                "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
                $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

              # Install Docker Engine and Compose
              apt-get update -y
              apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

              # Enable Docker service
              systemctl enable docker
              systemctl start docker

              # Add ubuntu user to docker group
              usermod -aG docker ubuntu

              # Create application directory
              mkdir -p /opt/asep
              chown ubuntu:ubuntu /opt/asep
              EOF

  tags = {
    Name        = "ASEP-Docker-Host-${var.environment}"
    Environment = var.environment
  }
}

# Elastic IP for stable DNS
resource "aws_eip" "asep_ip" {
  instance = aws_instance.asep_server.id
  domain   = "vpc"

  tags = {
    Name        = "asep-eip"
    Environment = var.environment
  }
}
