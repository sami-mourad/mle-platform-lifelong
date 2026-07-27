output "vpc_id" {
  value = aws_vpc.this.id
}

output "artifact_bucket" {
  value = aws_s3_bucket.artifacts.bucket
}

output "metadata_database_endpoint" {
  value     = aws_db_instance.metadata.address
  sensitive = true
}

output "redis_primary_endpoint" {
  value     = aws_elasticache_replication_group.online_state.primary_endpoint_address
  sensitive = true
}

output "ecr_repository_urls" {
  value = { for name, repository in aws_ecr_repository.services : name => repository.repository_url }
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.this.name
}
