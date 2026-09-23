locals {
  project_id = var.gcp_project_id
  region     = var.gcp_region

  topic_names = {
    gmail_notifications = "new-email"
    new-suggestion      = "new-suggestion"
    analysis_requests   = "analysis-request"
    analysis_results    = "suggestion-analysis"
  }
}

data "google_project" "current" {
  project_id = local.project_id
}
