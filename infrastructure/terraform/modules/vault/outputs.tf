output "service_account_name" { value = kubernetes_service_account.vault_auth.metadata[0].name }
output "namespace"            { value = kubernetes_namespace.vault.metadata[0].name }
