/**
 * Root outputs — consumed by CD pipeline and helm provider (ADR-0009).
 */

output "gke_endpoint" {
  description = "GKE cluster API endpoint"
  value       = module.gke.endpoint
  sensitive   = true
}

output "gke_cluster_name" {
  description = "GKE cluster name"
  value       = module.gke.cluster_name
}

output "audit_bucket_name" {
  description = "GCS WORM audit bucket name (spec 17, ADR-0024)"
  value       = module.audit_storage.bucket_name
}

output "vault_service_account" {
  description = "Kubernetes service account for Vault (ADR-0023)"
  value       = module.vault.service_account_name
}
