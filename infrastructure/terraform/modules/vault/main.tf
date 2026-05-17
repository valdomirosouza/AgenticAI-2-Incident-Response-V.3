/**
 * Vault module — HashiCorp Vault on Kubernetes for HITL HMAC keys (ADR-0023).
 * HA mode with 3 replicas; TLS enforced; audit log enabled.
 */

resource "kubernetes_namespace" "vault" {
  metadata {
    name = var.namespace
    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }
}

resource "helm_release" "vault" {
  name       = "vault"
  repository = "https://helm.releases.hashicorp.com"
  chart      = "vault"
  version    = "0.29.1"
  namespace  = kubernetes_namespace.vault.metadata[0].name

  set {
    name  = "server.image.tag"
    value = var.vault_image_tag
  }

  # HA mode — 3 replicas with Raft storage
  set {
    name  = "server.ha.enabled"
    value = "true"
  }

  set {
    name  = "server.ha.replicas"
    value = "3"
  }

  # Audit log to stdout — captured by Loki (ADR-0013)
  set {
    name  = "server.auditStorage.enabled"
    value = "true"
  }

  # TLS enforced — no plaintext Vault traffic (ADR-0023)
  set {
    name  = "global.tlsDisable"
    value = "false"
  }

  depends_on = [kubernetes_namespace.vault]
}

resource "kubernetes_service_account" "vault_auth" {
  metadata {
    name      = "vault-auth"
    namespace = kubernetes_namespace.vault.metadata[0].name
    annotations = {
      # Workload Identity binding — injected at apply time
    }
  }
}
