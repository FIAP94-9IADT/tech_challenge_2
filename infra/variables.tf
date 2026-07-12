variable "project_id" {
  description = "ID do projeto no GCP"
  type        = string
}

variable "region" {
  description = "Região usada para provisionar os recursos"
  type        = string
  default     = "us-central1"
}

variable "backend_image" {
  description = "Imagem do backend no Artifact Registry"
  type        = string
}

variable "frontend_image" {
  description = "Imagem do frontend no Artifact Registry"
  type        = string
}
