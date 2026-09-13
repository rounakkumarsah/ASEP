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

variable "aws_region" {
  description = "AWS region for the deployment"
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 Instance type"
  default     = "t3.xlarge" # Enterprise workloads require sufficient memory (Neo4j, Qdrant, etc.)
}

variable "key_name" {
  description = "Name of an existing EC2 KeyPair to enable SSH access"
  type        = string
  default     = ""
}

# Fetch the latest Ubuntu 22.04 LTS AMI
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

# Security Group for the Enterprise Stack
resource "aws_security_group" "asep_sg" {
  name        = "asep-enterprise-sg"
  description = "Allow inbound traffic for ASEP Stack"

  # SSH
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Frontend Fallback (if not routed through Traefik port 80)
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Backend Fallback
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EC2 Instance
resource "aws_instance" "asep_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  key_name      = var.key_name != "" ? var.key_name : null

  vpc_security_group_ids = [aws_security_group.asep_sg.id]

  root_block_device {
    volume_size = 50
    volume_type = "gp3"
  }

  user_data = <<-EOF
    #!/bin/bash
    set -e
    exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
    
    echo "Updating system..."
    apt-get update -y
    apt-get upgrade -y
    
    echo "Installing Git & curl..."
    apt-get install -y git curl

    echo "Cloning repository..."
    # You can update this URL to your private/public enterprise repo
    git clone https://github.com/rounakkumarsah/ASEP.git /opt/asep
    cd /opt/asep

    echo "Running setup script..."
    chmod +x setup.sh
    ./setup.sh
  EOF

  tags = {
    Name = "ASEP-Enterprise-Server"
  }
}

output "public_ip" {
  description = "Public IP of the deployed EC2 instance"
  value       = aws_instance.asep_server.public_ip
}

output "application_url" {
  description = "Direct HTTP URL to access the deployed application"
  value       = "http://${aws_instance.asep_server.public_ip}"
}
