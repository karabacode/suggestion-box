resource "google_cloud_run_v2_service" "agent" {
  name     = "suggestion-agent"
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
      min_instance_count = 1
    }

    containers {
      image = var.images.agent

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
        name  = "MODEL_NAME"
        value = var.model_name
      }
      env {
        name  = "OUTPUT_TOPIC"
        value = google_pubsub_topic.topic["analysis_results"].id
      }
      env {
        name = "MODEL_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.model.secret_id
            version = "latest"
          }
        }
      }
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  # Prevent Terraform from overwriting the image back to 'hello' once CI/CD starts updating it
  lifecycle {
    ignore_changes = [
      template[0].containers[0].image
    ]
  }
}
