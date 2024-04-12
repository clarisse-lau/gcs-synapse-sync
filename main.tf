# Generates an archive of the source code compressed as a .zip file.
data "archive_file" "source" {
  type        = "zip"
  source_dir  = "./src"
  output_path = "${path.module}/function.zip"
}

# Add source code zip to the Cloud Function's bucket (Cloud_function_bucket) 
resource "google_storage_bucket_object" "zip" {
  source       = data.archive_file.source.output_path
  content_type = "application/zip"
  name         = "src-${data.archive_file.source.output_md5}.zip"
  bucket       = var.dcc_bucket
  depends_on = [
    data.archive_file.source
  ]
}

# Create new storage bucket for the HTAN center

resource "google_storage_bucket" "static" {
 name          = var.center_bucket
 location      = "us"
 project       = var.project_id
 storage_class = "STANDARD"

 uniform_bucket_level_access = true
 cors {
  origin          = ["*"]
  method          = ["GET", "HEAD", "PUT", "POST"]
  response_header = ["*"]
  max_age_seconds = 3000
}
}

# Upload owner.txt files to the bucket
resource "google_storage_bucket_object" "default" {
 name         = "owner.txt"
 source       = "./owner.txt"
 content_type = "text/plain"
 bucket       = google_storage_bucket.static.id
}

# Give Synapse service account permission to access bucket
resource "google_storage_bucket_iam_member" "member" {
  bucket = google_storage_bucket.static.name
  role   = "roles/storage.legacyBucketReader"
  member = var.synapse_sa
}

resource "google_storage_bucket_iam_member" "member_writer" {
  bucket = google_storage_bucket.static.name
  role   = "roles/storage.legacyBucketWriter"
  member = var.synapse_sa
}

resource "google_storage_bucket_iam_member" "member_viewer" {
  bucket = google_storage_bucket.static.name
  role   = "roles/storage.objectViewer"
  member = var.synapse_sa
}

# Create the Cloud function triggered by a `Finalize` event on the bucket
resource "google_cloudfunctions_function" "Cloud_function_add" {
  name                  = "${var.center_bucket}-add"
  description           = "Cloud function triggered by file upload to gs://${var.center_bucket}"
  runtime               = "python311"
  project               = var.project_id
  region                = var.region
  available_memory_mb   = 512
  source_archive_bucket = var.dcc_bucket
  source_archive_object = google_storage_bucket_object.zip.name
  timeout               = 540
  entry_point           = "obj_add"
  environment_variables = {
    synapseProjectId = var.synapse_project_id
    gcProjectName = var.project_id
  }
  event_trigger {
    event_type = "google.storage.object.finalize"
    resource   = var.center_bucket
  }
  service_account_email = var.function_sa
  depends_on = [
    google_storage_bucket_object.zip
  ]
}

# Create the Cloud function triggered by a `Delete` event on the bucket
resource "google_cloudfunctions_function" "Cloud_function_delete" {
  name                  = "${var.center_bucket}-delete"
  description           = "Cloud function triggered by file deletion from gs://${var.center_bucket}"
  runtime               = "python311"
  project               = var.project_id
  region                = var.region
  available_memory_mb   = 512
  source_archive_bucket = var.dcc_bucket
  source_archive_object = google_storage_bucket_object.zip.name
  timeout               = 540
  entry_point           = "obj_delete"
  environment_variables = {
    synapseProjectId = var.synapse_project_id
    gcProjectName = var.project_id
  }
  event_trigger {
    event_type = "google.storage.object.delete"
    resource   = var.center_bucket
  }
  service_account_email = var.function_sa
  depends_on = [
    google_storage_bucket_object.zip
  ]
}