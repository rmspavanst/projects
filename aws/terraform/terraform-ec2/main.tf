provider "aws" {
  region = "ap-southeast-5"
}

resource "aws_security_group" "webserver_sg" {
  name        = "webserver_sg"
  description = "Allow ports for webserver"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "appserver_sg" {
  name        = "appserver_sg"
  description = "Allow ports for appserver"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 5000
    to_port     = 5001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "debserver_sg" {
  name        = "debserver_sg"
  description = "Allow ports for debserver"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "webserver" {
  ami           = "ami-0c4a807cb1a258810"
  instance_type = "t3.micro"
  key_name      = "rmsmy" # Reference to the existing key pair
  subnet_id     = "subnet-0792f85a382e26b19"
  vpc_security_group_ids = [aws_security_group.webserver_sg.id]
  tags = {
    Name = "webserver"
  }

  user_data = <<-EOF
  #!/bin/bash
  useradd -m -s /bin/bash -p $(openssl passwd -1 ansible) ansible
  usermod -aG wheel ansible
  echo "ansible ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/ansible
  sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
  sudo systemctl restart sshd
  EOF
}

resource "aws_instance" "appserver" {
  ami           = "ami-0c4a807cb1a258810"
  instance_type = "t3.micro"
  key_name      = "rmsmy" # Reference to the existing key pair
  subnet_id     = "subnet-0792f85a382e26b19"
  vpc_security_group_ids = [aws_security_group.appserver_sg.id]
  tags = {
    Name = "appserver"
  }

  user_data = <<-EOF
  #!/bin/bash
  useradd -m -s /bin/bash -p $(openssl passwd -1 ansible) ansible
  usermod -aG wheel ansible
  echo "ansible ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/ansible
  sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
  sudo systemctl restart sshd
  EOF
}

resource "aws_instance" "debserver" {
  ami           = "ami-0c4a807cb1a258810"
  instance_type = "t3.micro"
  key_name      = "rmsmy" # Reference to the existing key pair
  subnet_id     = "subnet-0792f85a382e26b19"
  vpc_security_group_ids = [aws_security_group.debserver_sg.id]
  tags = {
    Name = "debserver"
  }

  user_data = <<-EOF
  #!/bin/bash
  useradd -m -s /bin/bash -p $(openssl passwd -1 ansible) ansible
  usermod -aG wheel ansible
  echo "ansible ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/ansible
  sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
  sudo systemctl restart sshd
  EOF
}

output "instance_details" {
  value = {
    webserver = {
      id           = aws_instance.webserver.id
      private_ip   = aws_instance.webserver.private_ip
      public_ip    = aws_instance.webserver.public_ip
    }
    appserver = {
      id           = aws_instance.appserver.id
      private_ip   = aws_instance.appserver.private_ip
      public_ip    = aws_instance.appserver.public_ip
    }
    debserver = {
      id           = aws_instance.debserver.id
      private_ip   = aws_instance.debserver.private_ip
      public_ip    = aws_instance.debserver.public_ip
    }
  }
}