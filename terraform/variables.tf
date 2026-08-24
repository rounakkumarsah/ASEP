variable "aws_region" {
  description = "The AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "The EC2 instance type for the Docker host"
  type        = string
  default     = "t3.xlarge" # 4 vCPU, 16GB RAM recommended for sandboxes + local LLMs
}

variable "domain_name" {
  description = "The domain name for the ASEP instance"
  type        = string
}

variable "ssh_public_key_path" {
  description = "Path to the SSH public key for instance access"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "environment" {
  description = "Deployment environment (e.g., production, staging)"
  type        = string
  default     = "production"
}
