output "server_ip" {
  description = "The public Elastic IP address of the ASEP server"
  value       = aws_eip.asep_ip.public_ip
}

output "ssh_command" {
  description = "Command to SSH into the server"
  value       = "ssh -i ~/.ssh/id_rsa ubuntu@${aws_eip.asep_ip.public_ip}"
}

output "dns_instructions" {
  description = "Instructions for DNS setup"
  value       = "Please point the A record for ${var.domain_name} to ${aws_eip.asep_ip.public_ip}"
}
