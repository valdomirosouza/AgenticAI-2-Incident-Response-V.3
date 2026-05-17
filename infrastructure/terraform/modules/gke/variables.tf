variable "project_id"   { type = string }
variable "region"       { type = string }
variable "cluster_name" { type = string }
variable "node_count"   { type = number; default = 3 }
variable "machine_type" { type = string; default = "e2-standard-4" }
