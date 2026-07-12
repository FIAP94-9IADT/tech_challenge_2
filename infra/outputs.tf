output "backend_url" {
  description = "URL pública do backend"
  value       = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  description = "URL pública do frontend"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "artifact_registry" {
  description = "Caminho base para push das imagens"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo.repository_id}"
}
