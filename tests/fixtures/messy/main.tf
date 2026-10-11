terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

variable "region" {}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
}

resource "aws_s3_bucket" "Logs" {
  bucket = "${var.bucket}"
}
