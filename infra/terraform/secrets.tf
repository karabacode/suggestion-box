resource "google_service_account" "runtime" {
  account_id   = var.runtime_service_account_id
  display_name = "Suggestion Box runtime service account"
  project      = local.project_id
}

resource "google_secret_manager_secret" "google_client" {
  project   = local.project_id
  secret_id = var.secret_ids.google_client_secret

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "google_client" {
  secret      = google_secret_manager_secret.google_client.id
  secret_data = var.secret_values.google_client_secret_json
}

resource "google_secret_manager_secret" "gmail_read" {
  project   = local.project_id
  secret_id = var.secret_ids.gmail_read_token

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "gmail_read" {
  secret      = google_secret_manager_secret.gmail_read.id
  secret_data = var.secret_values.gmail_read_token_json
}

resource "google_secret_manager_secret" "gmail_send" {
  project   = local.project_id
  secret_id = var.secret_ids.gmail_send_token

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "gmail_send" {
  secret      = google_secret_manager_secret.gmail_send.id
  secret_data = var.secret_values.gmail_send_token_json
}

resource "google_secret_manager_secret" "maintenance" {
  project   = local.project_id
  secret_id = var.secret_ids.maintenance_password

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "maintenance" {
  secret      = google_secret_manager_secret.maintenance.id
  secret_data = var.secret_values.maintenance_password
}

resource "google_secret_manager_secret" "model" {
  project   = local.project_id
  secret_id = var.secret_ids.model_api_key

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "model" {
  secret      = google_secret_manager_secret.model.id
  secret_data = var.secret_values.model_api_key
}

resource "google_secret_manager_secret" "cloudflare" {
  project   = local.project_id
  secret_id = var.cloudflare_secret_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "cloudflare" {
  secret      = google_secret_manager_secret.cloudflare.id
  secret_data = var.cloudflare_api_token
}
