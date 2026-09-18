resource "google_cloud_run_v2_service" "dispatcher" {
  name     = "suggestion-response-dispatcher"
  project  = local.project_id
  location = local.region
  deletion_protection = false
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account                  = google_service_account.runtime.email
    max_instance_request_concurrency = 80
    timeout                          = "300s"

    scaling {
      max_instance_count = 3
    }

    containers {
      image = var.images.dispatcher

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
        name  = "GOOGLE_REDIRECT_URI"
        value = var.oauth_redirect_uris.dispatcher
      }
      env {
        name  = "MAINTENANCE_USERNAME"
        value = "maintenance"
      }
      env {
        name  = "GMAIL_SCOPES"
        value = "https://www.googleapis.com/auth/gmail.send"
      }
      env {
        name  = "GMAIL_ACCOUNT_EMAIL"
        value = var.gmail_account_email
      }
      env {
        name = "GOOGLE_CLIENT_SECRET_JSON"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.google_client.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "GMAIL_TOKEN_JSON"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gmail_send.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "MAINTENANCE_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.maintenance.secret_id
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
