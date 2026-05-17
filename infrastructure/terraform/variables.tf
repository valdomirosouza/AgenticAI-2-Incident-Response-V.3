/**
 * Input variables — all sensitive values injected at plan/apply time (RULE-C03).
 */

variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region for all resources"
  type        = string
  default     = "southamerica-east1"
}

variable "cluster_name" {
  description = "GKE cluster name"
  type        = string
  default     = "incident-response-copilot"
}

variable "node_count" {
  description = "Number of nodes per zone in the default node pool"
  type        = number
  default     = 3
}

variable "machine_type" {
  description = "GCE machine type for GKE nodes"
  type        = string
  default     = "e2-standard-4"
}

variable "audit_bucket_name" {
  description = "GCS bucket name for WORM audit trail (spec 17, ADR-0024)"
  type        = string
}

variable "vault_namespace" {
  description = "Kubernetes namespace for Vault deployment"
  type        = string
  default     = "vault"
}

variable "vault_image_tag" {
  description = "HashiCorp Vault image tag — pinned for supply chain integrity (ADR-0022)"
  type        = string
  default     = "1.18.3"
}
