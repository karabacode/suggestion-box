resource "google_project_service" "required" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "iamcredentials.googleapis.com",
    "pubsub.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
  ])

  project            = local.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "cloud_run_source" {
  project       = local.project_id
  location      = local.region
  repository_id = "cloud-run-source-deploy"
  format        = "DOCKER"
  description   = "Cloud Run Source Deployments"
}

resource "google_storage_bucket" "run_sources" {
  project                     = local.project_id
  name                        = "run-sources-suggestion-box-508020-northamerica-northeast1"
  location                    = "NORTHAMERICA-NORTHEAST1"
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  force_destroy               = false

  soft_delete_policy {
    retention_duration_seconds = 604800
  }
}
