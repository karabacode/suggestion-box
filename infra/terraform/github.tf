# 1. Enable required Google APIs
resource "google_project_service" "iam_credentials" {
  project = local.project_id
  service = "iamcredentials.googleapis.com"

  disable_on_destroy = false
}

# 2. Workload Identity Pool
resource "google_iam_workload_identity_pool" "github" {
  project                   = local.project_id
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions Pool"
  description               = "Workload Identity Pool for GitHub Actions CI/CD"
  
  depends_on = [google_project_service.iam_credentials]
}

# 3. Workload Identity Provider for GitHub OIDC
resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"
  display_name                       = "GitHub Provider"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  # Use assertion.repository directly in the condition
  attribute_condition = "assertion.repository == '${var.github_repository}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# 4. Service Account for GitHub Actions
resource "google_service_account" "github_deployer" {
  project      = local.project_id
  account_id   = "github-deployer"
  display_name = "GitHub Actions Deployer"
}

# 5. Grant Roles to the Service Account
resource "google_project_iam_member" "github_deployer_artifact_registry" {
  project = local.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.github_deployer.email}"
}

resource "google_project_iam_member" "github_deployer_run_admin" {
  project = local.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.github_deployer.email}"
}

resource "google_project_iam_member" "github_deployer_sa_user" {
  project = local.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.github_deployer.email}"
}

resource "google_service_account_iam_member" "github_wif_binding" {
  service_account_id = google_service_account.github_deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repository}"
}