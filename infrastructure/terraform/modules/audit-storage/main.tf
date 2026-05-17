/**
 * GCS WORM audit storage module — spec 17 §3.2, ADR-0024.
 * Object retention lock enforces 2-year minimum retention; no delete or overwrite allowed.
 */

resource "google_storage_bucket" "audit_trail" {
  name                        = var.bucket_name
  location                    = var.region
  project                     = var.project_id
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true

  # WORM: Object Retention Lock — each object sets its own retain-until date (ADR-0024)
  enable_object_retention = true

  # Versioning — retained even after object retention expires
  versioning {
    enabled = true
  }

  # Prevent accidental Terraform-triggered deletion
  lifecycle {
    prevent_destroy = true
  }

  # Minimum retention enforced at bucket level as belt-and-suspenders
  retention_policy {
    is_locked        = true
    retention_period = 63072000 # 2 years in seconds — ADR-0024
  }
}

# IAM: only the audit-writer service account may create objects — no delete permission
resource "google_storage_bucket_iam_member" "audit_writer" {
  bucket = google_storage_bucket.audit_trail.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${var.audit_writer_sa_email}"
}

resource "google_storage_bucket_iam_member" "audit_reader" {
  bucket = google_storage_bucket.audit_trail.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${var.audit_reader_sa_email}"
}
