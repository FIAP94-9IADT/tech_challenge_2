output "resource_group_name" {
  description = "Nome do Resource Group provisionado"
  value = azurerm_resource_group.main.name
}

output "workspace_name" {
  description = "Nome do workspace do Azure Machine Learning"
  value = azurerm_machine_learning_workspace.main.name
}

output "subscription_id" {
  description = "Identificador da assinatura usada pelo provider"
  value       = data.azurerm_client_config.current.subscription_id
}

output "location" {
  description = "Região do workspace"
  value       = azurerm_resource_group.main.location
}

output "compute_cluster_name" {
  description = "Nome do cluster de sweep, quando sua criação estiver habilitada"
  value       = var.create_compute_cluster ? azurerm_machine_learning_compute_cluster.cpu[0].name : null
}
