variable "environment" {}
variable "security_groups" {
  type = "list"
}
variable "subnets" {
  type = "list"
}
variable "vpc_id" {}

variable "SITE_HOST" {}

variable "proxy_server_ids" {
  type = "list"
}

variable "account_id" {}
variable "ssl_policy" {}
