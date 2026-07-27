# AWS Foundation Blueprint

This Terraform creates the durable foundation rather than pretending one generic service definition fits every organization:

- VPC and public/private subnets;
- encrypted/versioned S3 artifact bucket;
- private PostgreSQL metadata database;
- encrypted Redis replication group;
- ECR repositories;
- ECS cluster and log groups.

It intentionally does not hard-code public ingress, identity provider, secret manager, TLS certificates, load balancer routing, or organization-specific ECS task/service policies. Those are environment decisions after the threat model, domains, and service ownership are known.

```bash
terraform init
terraform fmt -check
terraform validate
export TF_VAR_database_password='replace-with-a-long-secret'
terraform plan -out platform.tfplan
```

Never commit state or secrets. Use a remote encrypted backend and CI identity in a real account.
