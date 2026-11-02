output "site_website_endpoint" {
  value = aws_s3_bucket_website_configuration.site.website_endpoint
}

output "site_bucket_name" {
  value = awscc_s3_bucket.site.bucket_name
}

output "ci_public_ip" {
  value = aws_eip.jenkins_eip.public_ip
}

output "app_public_dns" {
  value = aws_eip.app_eip.public_dns
}

output "app_private_dns" {
  value = aws_instance.app.private_dns
}

output "db_private_ip" {
  value = aws_instance.db.private_ip
}

output "backend_ecr_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "mongo_ecr_url" {
  value = aws_ecr_repository.mongo.repository_url
}
