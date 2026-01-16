variable "bucket" {
  description = "The name of the bucket"
  type        = string
}

variable "tags" {
  type    = map(any)
  default = {}
}

variable "tags_all" {
  type    = map(any)
  default = {}
}

# S3 bucket
resource "aws_s3_bucket" "main" {
  bucket = var.bucket

  tags     = var.tags != {} ? var.tags : {}
  tags_all = var.tags_all != {} ? var.tags_all : {}
}
