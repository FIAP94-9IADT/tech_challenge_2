terraform {
  required_version = ">= 1.5.0"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.0" }
    random  = { source = "hashicorp/random", version = "~> 3.6" }
  }
}

provider "azurerm" {
  features {}
}

data "azurerm_client_config" "current" {
}

resource "random_string" "suffix" {
  length  = 6
  upper   = false
  special = false
}

locals {
  suffix = random_string.suffix.result
  tags = {
    project = "hospital-routes"
    purpose = "academic"
  }
}

resource "azurerm_resource_group" "main" {
  name     = "${var.name_prefix}-rg-${local.suffix}"
  location = var.location
  tags     = local.tags
}

resource "azurerm_storage_account" "main" {
  name                     = "${replace(var.name_prefix, "-", "")}st${local.suffix}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  tags                     = local.tags
}

resource "azurerm_key_vault" "main" {
  name                       = "${var.name_prefix}-kv-${local.suffix}"
  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false
  tags                       = local.tags
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.name_prefix}-log-${local.suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.tags
}

resource "azurerm_application_insights" "main" {
  name                = "${var.name_prefix}-appi-${local.suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.main.id
  tags                = local.tags
}

resource "azurerm_machine_learning_workspace" "main" {
  name                    = "${var.name_prefix}-mlw-${local.suffix}"
  resource_group_name     = azurerm_resource_group.main.name
  location                = azurerm_resource_group.main.location
  application_insights_id = azurerm_application_insights.main.id
  key_vault_id            = azurerm_key_vault.main.id
  storage_account_id      = azurerm_storage_account.main.id
  public_network_access_enabled = true
  identity {
    type = "SystemAssigned"
  }
  tags = local.tags
}

resource "azurerm_machine_learning_compute_cluster" "cpu" {
  name                          = "cpu-cluster"
  location                      = azurerm_resource_group.main.location
  machine_learning_workspace_id = azurerm_machine_learning_workspace.main.id
  vm_priority                   = "LowPriority"
  vm_size                       = var.compute_vm_size
  description                   = "Cluster escalável para o sweep do algoritmo genético"
  ssh_public_access_enabled     = false
  scale_settings {
    min_node_count                       = 0
    max_node_count                       = var.max_compute_nodes
    scale_down_nodes_after_idle_duration = "PT2M"
  }
  identity {
    type = "SystemAssigned"
  }
  tags = local.tags
}
