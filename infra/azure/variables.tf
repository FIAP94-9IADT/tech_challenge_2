variable "location" {
  description = "Região Azure dos recursos"
  type        = string
  default     = "brazilsouth"
}

variable "name_prefix" {
  description = "Prefixo curto para os nomes dos recursos"
  type        = string
  default     = "hosp-routes"
}

variable "compute_vm_size" {
  description = "SKU dos nós usados pelo sweep"
  type        = string
  default     = "Standard_DS2_v2"
}

variable "max_compute_nodes" {
  description = "Limite de nós paralelos; zero nós são mantidos quando o cluster está ocioso"
  type        = number
  default     = 4
  validation {
    condition     = var.max_compute_nodes >= 1 && var.max_compute_nodes <= 4
    error_message = "Use entre um e quatro nós para limitar o custo acadêmico."
  }
}
