resource "aws_instance" "web" {
  count         = var.instance_count
  ami           = "ami-0123456789abcdef0"
  instance_type = "t3.micro"

  tags = {
    Name = "${var.name}-web-${count.index}"
  }
}
