terraform {
  required_version = ">= 1.5.0"
  required_providers {
    docker = { source = "kreuzwerker/docker", version = "~> 3.0" }
  }
}

provider "docker" {}

resource "docker_image" "optimizer" {
  name = "hospital-routes:local"
  build { context = "${path.module}/.." }
}

resource "docker_container" "optimizer" {
  name  = "hospital-routes"
  image = docker_image.optimizer.image_id
  volumes {
    host_path      = abspath("${path.module}/../outputs")
    container_path = "/app/outputs"
  }
}
