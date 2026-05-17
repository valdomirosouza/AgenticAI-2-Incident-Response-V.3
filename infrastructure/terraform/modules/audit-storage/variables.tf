variable "project_id"           { type = string }
variable "region"               { type = string }
variable "bucket_name"          { type = string }
variable "audit_writer_sa_email" { type = string; default = "" }
variable "audit_reader_sa_email" { type = string; default = "" }
