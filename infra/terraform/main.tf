terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
    awscc = {
      source = "hashicorp/awscc"
    }
  }

  backend "s3" {
    bucket       = "ict381-eca-tfstate-xxingyao-203635632743-us-east-1-an"
    key          = "eca/terraform.tfstate"
    region       = "us-east-1"
    use_lockfile = true
  }
}

provider "aws" {
  region = "us-east-1"
}

provider "awscc" {
  region = "us-east-1"
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# ---------------- Security groups ----------------

resource "aws_security_group" "ci_sg" {
  description = "CI host - Jenkins"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port = 8080
    to_port   = 8080
    protocol  = "tcp"
    cidr_blocks = [
      "9.234.106.48/28",
      "9.234.98.160/28",
      "9.234.98.176/28",
      "192.30.252.0/22",
      "185.199.108.0/22",
      "140.82.112.0/20",
      "143.55.64.0/20",
    ]
    ipv6_cidr_blocks = [
      "2a0a:a440::/29",
      "2606:50c0::/32",
    ]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "ci-sg"
  }
}

resource "aws_security_group" "application_sg" {
  description = "Application host - backend API"

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.ci_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "application-sg"
  }
}

resource "aws_security_group" "database_sg" {
  description = "Database host - MongoDB"

  ingress {
    from_port       = 27017
    to_port         = 27017
    protocol        = "tcp"
    security_groups = [aws_security_group.application_sg.id]
  }

  ingress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.ci_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "database-sg"
  }
}

# ---------------- EC2 instances ----------------

resource "aws_instance" "jenkins" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.large"
  key_name               = "vockey"
  vpc_security_group_ids = [aws_security_group.ci_sg.id]
  iam_instance_profile   = "LabInstanceProfile"

  root_block_device {
    volume_size = 32
  }

  tags = {
    Name  = "jenkins"
    group = "jenkins"
  }
}

resource "aws_instance" "app" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.large"
  key_name               = "vockey"
  vpc_security_group_ids = [aws_security_group.application_sg.id]
  iam_instance_profile   = "LabInstanceProfile"

  root_block_device {
    volume_size = 32
  }

  tags = {
    Name  = "app"
    group = "web"
  }
}

resource "aws_instance" "db" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t3.large"
  key_name                    = "vockey"
  vpc_security_group_ids      = [aws_security_group.database_sg.id]
  iam_instance_profile        = "LabInstanceProfile"
  associate_public_ip_address = true # outbound only (ECR, apt); inbound limited by database_sg

  root_block_device {
    volume_size = 32
  }

  tags = {
    Name  = "db"
    group = "database"
  }
}

# ---------------- Elastic IPs ----------------

resource "aws_eip" "jenkins_eip" {
  instance = aws_instance.jenkins.id
  domain   = "vpc"
}

resource "aws_eip" "app_eip" {
  instance = aws_instance.app.id
  domain   = "vpc"
}

# ---------------- S3 static website ----------------
# The bucket uses awscc_s3_bucket (hashicorp/awscc) instead of aws_s3_bucket. After creating a bucket,
# aws_s3_bucket reads back its Object Lock setting (s3:GetBucketObjectLockConfiguration), which the
# Learner Lab denies. The website, access block and policy are ordinary aws provider resources.

resource "awscc_s3_bucket" "site" {
  bucket_name = "ict381-eca-site-xxingyao-203635632743"
}

resource "aws_s3_bucket_website_configuration" "site" {
  bucket = awscc_s3_bucket.site.bucket_name

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

resource "aws_s3_bucket_public_access_block" "site" {
  bucket                  = awscc_s3_bucket.site.bucket_name
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "site" {
  bucket     = awscc_s3_bucket.site.bucket_name
  depends_on = [aws_s3_bucket_public_access_block.site]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "PublicRead"
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:GetObject"
      Resource  = "${awscc_s3_bucket.site.arn}/*"
    }]
  })
}

# ---------------- ECR repositories ----------------

resource "aws_ecr_repository" "backend" {
  name                 = "ict381_backend"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}

resource "aws_ecr_repository" "mongo" {
  name                 = "ict381_mongo"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}
