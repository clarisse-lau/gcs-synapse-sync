variable "project_id" {
  type    = string
  description = "The ID of the project where the resources will be created"
  default = "<YOUR-PROJECT-ID>"
}

variable "region" {
  type    = string
  description = "The region in which resources will be applied"
  default = "europe-west2"
}

variable "center_bucket" {
  type    = string
  description = "Name of new Google Bucket to which file additions and deletions will trigger function"
  default = ""
}

variable "dcc_bucket" {
  type    = string
  description = "Name of existing DCC bucket to store function source code"
  default = "gcptosynapse"
}

variable "synapse_sa" {
  type    = string
  description = "Name of Synapse Service Account to grant access to bucket"
  default = ""
}

variable "function_sa" {
  type    = string
  description = "ID of Google Service Account to be used by Cloud Function"
  default = ""
}

variable "synapse_project_id" {
  type    = string
  description = "ID of Synapse project to sync files to"
  default = ""
}