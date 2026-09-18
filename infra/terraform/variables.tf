variable "gcp_project_id" {
  type    = string
  default = "suggestion-box-508020"
}

variable "gcp_region" {
  type    = string
  default = "northamerica-northeast1"
}

variable "images" {
  type = object({
    ingester   = string
    core       = string
    agent      = string
    dispatcher = string
  })
  description = "Container images for the Cloud Run services."
}

variable "runtime_service_account_id" {
  type    = string
  default = "suggestion-box-runtime"
}

variable "secret_ids" {
  type = object({
    google_client_secret = string
    gmail_read_token     = string
    gmail_send_token     = string
    maintenance_password = string
    model_api_key        = string
  })
  description = "Secret Manager secret IDs to create and populate during deployment."
}

variable "secret_values" {
  type = object({
    google_client_secret_json = string
    gmail_read_token_json     = string
    gmail_send_token_json     = string
    maintenance_password      = string
    model_api_key             = string
  })
  description = "Sensitive secret payloads for the runtime services. Keep this in local terraform.tfvars only."
  sensitive   = true
}

variable "cloudflare_account_id" {
  type      = string
  sensitive = true
}

variable "cloudflare_api_token" {
  type      = string
  sensitive = true
}

variable "cloudflare_secret_id" {
  type    = string
  default = "cloudflare-api-token"
}

variable "cloudflare_d1_database_name" {
  type        = string
  description = "Name of the Cloudflare D1 database Terraform should create."
}

variable "gmail_account_email" {
  type = string
}

variable "model_name" {
  type    = string
  default = "gemini-3.6-flash"
}

variable "oauth_redirect_uris" {
  type = object({
    ingester   = string
    dispatcher = string
  })
}

variable "maintenance_user" {
  type = string
  default = "maintenance"
  description = "username for maintenance"
}

variable "scope_read" {
  type = string
  description = "scope for the secret token"
}

variable "ignored_emails_labels" {
  type = string
  description = "labels ignore when reading from gmail"
}

variable "github_repository" {
  type        = string
  description = "GitHub repository in the format owner/repo (e.g., username/suggestion-box)"
}
