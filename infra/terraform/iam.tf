resource "google_project_iam_member" "runtime_pubsub_publisher" {
  project = local.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_project_iam_member" "pubsub_service_agent_token_creator" {
  project = local.project_id
  role    = "roles/iam.serviceAccountTokenCreator"
  member  = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_cloud_run_v2_service_iam_member" "runtime_invokes_core" {
  name     = google_cloud_run_v2_service.core.name
  location = local.region
  project  = local.project_id
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_cloud_run_v2_service_iam_member" "runtime_invokes_ingester" {
  name     = google_cloud_run_v2_service.ingester.name
  location = local.region
  project  = local.project_id
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_cloud_run_v2_service_iam_member" "runtime_invokes_agent" {
  name     = google_cloud_run_v2_service.agent.name
  location = local.region
  project  = local.project_id
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_cloud_run_v2_service_iam_member" "runtime_invokes_dispatcher" {
  name     = google_cloud_run_v2_service.dispatcher.name
  location = local.region
  project  = local.project_id
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "runtime_secret_access" {
  for_each = {
    google_client = google_secret_manager_secret.google_client.id
    gmail_read    = google_secret_manager_secret.gmail_read.id
    gmail_send    = google_secret_manager_secret.gmail_send.id
    maintenance   = google_secret_manager_secret.maintenance.id
    model         = google_secret_manager_secret.model.id
    cloudflare    = google_secret_manager_secret.cloudflare.id
  }

  secret_id = each.value
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}
