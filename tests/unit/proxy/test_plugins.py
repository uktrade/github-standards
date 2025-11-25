import pytest

from proxy.http.exception import HttpRequestRejected
from unittest import mock


from src.proxy.plugins import OutgoingRequestInterceptorPlugin


class TestOutgoingRequestInterceptorPlugin:
    def test_no_endpoint_in_flags_throws_http_exception(self):
        flags = mock.MagicMock()
        plugin = OutgoingRequestInterceptorPlugin("test_plugin", flags, None, None)

        request = mock.MagicMock()
        with pytest.raises(HttpRequestRejected):
            plugin.before_upstream_connection(request=request)

    def test_requested_endpoint_does_not_exist_in_endpoints_in_flags_throws_http_exception(self):
        flags = mock.MagicMock(allowed_trufflehog_vendor_endpoints="something.com")
        plugin = OutgoingRequestInterceptorPlugin("test_plugin", flags, None, None)

        request = mock.MagicMock(host="something-else.com".encode())
        with pytest.raises(HttpRequestRejected):
            plugin.before_upstream_connection(request=request)

    def test_requested_endpoint_exists_in_endpoints_in_flags_returns_request(self):
        flags = mock.MagicMock(allowed_trufflehog_vendor_endpoints="something.com")
        plugin = OutgoingRequestInterceptorPlugin("test_plugin", flags, None, None)

        request = mock.MagicMock(host="something.com".encode())

        assert plugin.before_upstream_connection(request=request) == request
