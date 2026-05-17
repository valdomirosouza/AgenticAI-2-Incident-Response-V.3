/**
 * GKE module — Autopilot cluster with workload identity (ADR-0009 blue-green, ADR-0003).
 * Argo Rollouts is installed separately via helm module.
 */

resource "google_container_cluster" "main" {
  name     = var.cluster_name
  location = var.region
  project  = var.project_id

  # Autopilot manages node pools — no manual node pool management needed
  enable_autopilot = true

  # Private cluster — nodes have no public IPs
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  # Workload Identity — pods authenticate to GCP APIs without static keys (ADR-0023)
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Binary Authorization — only signed images (ADR-0022 SLSA Level 2)
  binary_authorization {
    evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
  }

  release_channel {
    channel = "REGULAR"
  }

  deletion_protection = true

  lifecycle {
    prevent_destroy = true
  }
}
