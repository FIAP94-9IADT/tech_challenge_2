output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "workspace_name" {
  value = azurerm_machine_learning_workspace.main.name
}

output "compute_cluster_name" {
  value = azurerm_machine_learning_compute_cluster.cpu.name
}
