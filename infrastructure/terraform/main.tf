/**
 * Root Terraform configuration — GKE + GCS WORM + Vault (ADR-0009, ADR-0023, ADR-0024).
 * All resource values are parameterised; no secrets or credentials in source (RULE-C03).
 */

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.17"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.35"
    }
  }

  backend "gcs" {
    # bucket and prefix supplied via -backend-config at init time — RULE-C03
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

provider "kubernetes" {
  host                   = module.gke.endpoint
  cluster_ca_certificate = base64decode(module.gke.cluster_ca_certificate)
  token                  = data.google_client_config.default.access_token
}

provider "helm" {
  kubernetes {
    host                   = module.gke.endpoint
    cluster_ca_certificate = base64decode(module.gke.cluster_ca_certificate)
    token                  = data.google_client_config.default.access_token
  }
}

data "google_client_config" "default" {}

# ── Modules ────────────────────────────────────────────────────────────────────

module "gke" {
  source = "./modules/gke"

  project_id   = var.gcp_project_id
  region       = var.gcp_region
  cluster_name = var.cluster_name
  node_count   = var.node_count
  machine_type = var.machine_type
}

module "audit_storage" {
  source = "./modules/audit-storage"

  project_id  = var.gcp_project_id
  region      = var.gcp_region
  bucket_name = var.audit_bucket_name
}

module "vault" {
  source = "./modules/vault"

  namespace        = var.vault_namespace
  vault_image_tag  = var.vault_image_tag
  depends_on       = [module.gke]
}
