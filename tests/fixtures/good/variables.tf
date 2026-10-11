variable "name" {
  description = "Prefix for every resource name."
  type        = string
}

variable "instance_count" {
  description = "How many instances to run."
  type        = number
  default     = 1
}
