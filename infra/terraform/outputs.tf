output "service_urls" {
  description = "Cloud Run URLs for application wiring and OAuth callback registration."
  value = {
    ingester   = google_cloud_run_v2_service.ingester.uri
    core       = google_cloud_run_v2_service.core.uri
    agent      = google_cloud_run_v2_service.agent.uri
    dispatcher = google_cloud_run_v2_service.dispatcher.uri
  }
}

output "pubsub_topics" {
  description = "Pub/Sub topic names used by the event pipeline."
  value       = { for key, topic in google_pubsub_topic.topic : key => topic.name }
}

output "artifact_registry_repository" {
  description = "Existing Artifact Registry repository used by Cloud Run builds."
  value       = google_artifact_registry_repository.cloud_run_source.name
}

output "wif_provider_name" {
  description = "Value for GCP_WIF_PROVIDER secret"
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "wif_service_account_email" {
  description = "Value for GCP_SA_EMAIL secret"
  value       = google_service_account.github_deployer.email
}