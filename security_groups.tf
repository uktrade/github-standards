

resource "aws_security_group_rule" "service_egress_https_to_everywhere" {
  description = "egress-https-from-service"

  security_group_id = 1
  cidr_blocks       = ["0.0.0.0/0"]

  type      = "egress"
  from_port = "443"
  to_port   = "443"
  protocol  = "tcp"
}
