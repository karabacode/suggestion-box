resource "google_cloud_run_v2_service" "ingester" {
  name     = "gmail-suggestion-ingester"
  project  = local.project_id
  location = local.region
  deletion_protection = false
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account                  = google_service_account.runtime.email
    max_instance_request_concurrency = 80
    timeout                          = "300s"

    scaling {
      max_instance_count = 3
    }

    containers {
      image = var.images.ingester

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
        name  = "REDIRECT_URI"
        value = var.oauth_redirect_uris.ingester
      }
      env {
        name  = "SCOPES"
        value = var.scope_read
      }
      env {
        name  = "PUBSUB_TOPIC"
        value = google_pubsub_topic.topic["gmail_notifications"].id
      }
      env {
        name  = "CORE_TOPIC"
        value = google_pubsub_topic.topic["new-suggestion"].id
      }
      env {
        name  = "MAINTENANCE_USERNAME"
        value = var.maintenance_user
      }
      env {
        name  = "DUPLICATE_SENDER_TTL_SECONDS"
        value = "60"
      }
      env {
        name  = "IGNORED_GMAIL_LABELS"
        value = var.ignored_emails_labels
      }

      env {
        name = "CLIENT_SECRET_JSON"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.google_client.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "TOKEN_JSON"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gmail_read.secret_id
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
