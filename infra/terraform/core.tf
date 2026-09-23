resource "google_cloud_run_v2_service" "core" {
  name     = "suggestion-core"
  project  = local.project_id
  location = local.region
  deletion_protection = false
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account                  = google_service_account.runtime.email
    max_instance_request_concurrency = 80
    timeout                          = "300s"

    containers {
      image = var.images.core

      ports {
        container_port = 8080
      }

      resources {
        cpu_idle = true
        limits = {
          cpu    = "1000m"
          memory = "512Mi"
        }
        startup_cpu_boost = true
      }
      env {
        name  = "CLOUDFLARE_ACCOUNT_ID"
        value = var.cloudflare_account_id
      }
      env {
        name  = "CLOUDFLARE_D1_DATABASE_ID"
        value = cloudflare_d1_database.suggestions.id
      }
      env {
        name = "CLOUDFLARE_API_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.cloudflare.secret_id
            version = "latest"
          }
        }
      }
    }
  }

  # Prevent Terraform from overwriting the image back to 'hello' once CI/CD starts updating it
  lifecycle {
    ignore_changes = [
      template[0].containers[0].image
    ]
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }
}
