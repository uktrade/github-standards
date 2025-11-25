from src.hooks.config import (
    LOGGER,
)
from typing import Optional

from proxy.http.proxy import HttpProxyBasePlugin
from proxy.http.parser import HttpParser
from proxy.http.exception import HttpRequestRejected
from proxy.common.flag import flags


logger = LOGGER

flags.add_argument(
    "--allowed-trufflehog-vendor-endpoints",
    type=str,
    default="",
    help="A comma separated list of endpoints that are allowed to be called by trufflehog",
)


class OutgoingRequestInterceptorPlugin(HttpProxyBasePlugin):
    def before_upstream_connection(
        self,
        request: HttpParser,
    ) -> Optional[HttpParser]:
        endpoint = request.host.decode("utf-8") if request.host else None
        logger.debug("Calling before_upstream_connection for host %s.", endpoint)

        allowed_endpoints = (
            self.flags.allowed_trufflehog_vendor_endpoints.split(",")
            if self.flags.allowed_trufflehog_vendor_endpoints
            else []
        )
        logger.debug("Allowed endpoints: %s", allowed_endpoints)

        if endpoint in allowed_endpoints:
            logger.debug("The endpoint %s is an allowed endpoint", endpoint)
            return request

        logger.info(
            "The endpoint %s is not an endpoint that has been configured for usage with this security scan", endpoint
        )
        raise HttpRequestRejected()
