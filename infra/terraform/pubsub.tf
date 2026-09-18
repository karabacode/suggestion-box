resource "google_pubsub_topic" "topic" {
  for_each = local.topic_names

  name       = each.value
  project    = local.project_id
  depends_on = [google_project_service.required]
}

resource "google_pubsub_topic_iam_member" "gmail_pubsub_publisher" {
  project = local.project_id
  topic   = "projects/suggestion-box-508020/topics/new-email"
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:gmail-api-push@system.gserviceaccount.com"
}

resource "google_pubsub_subscription" "gmail_to_ingester" {
  name    = "new-email-sub"
  project = local.project_id
  topic   = google_pubsub_topic.topic["gmail_notifications"].id

  ack_deadline_seconds       = 30
  message_retention_duration = "604800s"

  push_config {
    push_endpoint = "${google_cloud_run_v2_service.ingester.uri}/v1/emails/"
    oidc_token {
      service_account_email = google_service_account.runtime.email
      audience              = google_cloud_run_v2_service.ingester.uri
    }
  }
}

resource "google_pubsub_subscription" "analysis_to_agent" {
  name    = "analysis-request-push"
  project = local.project_id
  topic   = google_pubsub_topic.topic["analysis_requests"].id

  ack_deadline_seconds       = 30
  message_retention_duration = "604800s"

  push_config {
    push_endpoint = "${google_cloud_run_v2_service.agent.uri}/webhooks/pubsub"
    oidc_token {
      service_account_email = google_service_account.runtime.email
      audience              = google_cloud_run_v2_service.agent.uri
    }
  }
}

resource "google_pubsub_subscription" "analysis_to_core" {
  name    = "suggestion-analysis-push"
  project = local.project_id
  topic   = google_pubsub_topic.topic["analysis_results"].id

  ack_deadline_seconds       = 30
  message_retention_duration = "604800s"

  push_config {
    push_endpoint = "${google_cloud_run_v2_service.core.uri}/webhooks/suggestion-analysis"
    oidc_token {
      service_account_email = google_service_account.runtime.email
      audience              = google_cloud_run_v2_service.core.uri
    }
  }
}
