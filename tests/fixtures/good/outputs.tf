output "instance_ids" {
  description = "IDs of the instances."
  value       = aws_instance.web[*].id
}
