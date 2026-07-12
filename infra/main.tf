# Infraestrutura do Tech Challenge Fase 2 no GCP.
# Recursos: Cloud Run, Artifact Registry e Secret Manager.

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# --- APIs necessárias -------------------------------------------------------

resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudbuild.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false
}

# --- Artifact Registry ------------------------------------------------------

resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "rotas-medicas"
  format        = "DOCKER"
  description   = "Imagens do Tech Challenge Fase 2 (backend Flask + frontend React)"

  depends_on = [google_project_service.apis]
}

# --- Secret Manager (chave da OpenAI) ---------------------------------------

resource "google_secret_manager_secret" "openai_key" {
  secret_id = "openai-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# O valor do secret é criado fora do Terraform para não ficar no state:
#   echo -n "sk-..." | gcloud secrets versions add openai-api-key --data-file=-

# --- Service Account do backend ---------------------------------------------

resource "google_service_account" "backend" {
  account_id   = "rotas-backend"
  display_name = "Backend do sistema de rotas médicas"
}

resource "google_secret_manager_secret_iam_member" "backend_secret_access" {
  secret_id = google_secret_manager_secret.openai_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend.email}"
}

# --- Cloud Run: backend -----------------------------------------------------

resource "google_cloud_run_v2_service" "backend" {
  name                = "rotas-backend"
  location            = var.region
  deletion_protection = false # projeto de demo/estudo, sem necessidade de proteção

  template {
    service_account = google_service_account.backend.email

    scaling {
      min_instance_count = 0 # suspende as instâncias quando não há requisições
      max_instance_count = 2
    }

    containers {
      image = var.backend_image

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.openai_key.secret_id
            version = "latest"
          }
        }
      }
    }
  }

  depends_on = [
    google_project_service.apis,
    google_secret_manager_secret_iam_member.backend_secret_access,
  ]
}

# --- Cloud Run: frontend ----------------------------------------------------

resource "google_cloud_run_v2_service" "frontend" {
  name                = "rotas-frontend"
  location            = var.region
  deletion_protection = false

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    containers {
      image = var.frontend_image

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }
  }

  depends_on = [google_project_service.apis]
}

# --- Acesso público (demo) --------------------------------------------------

resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  name     = google_cloud_run_v2_service.backend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  name     = google_cloud_run_v2_service.frontend.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
