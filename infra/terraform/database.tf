resource "cloudflare_d1_database" "suggestions" {
  account_id = var.cloudflare_account_id
  name       = var.cloudflare_d1_database_name
}