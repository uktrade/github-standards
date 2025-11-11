from src.hooks.trufflehog.vendors import AWS, AllowedTrufflehogVendor, CircleCI, Datadog, Github, Gitlab, Jira, Okta, Slack


class BaseVendorTests:
    cls = None
    expected_code = None
    expected_endpoints = None

    def test_code(self):
        assert self.cls().code == self.expected_code

    def test_endpoints(self):
        assert self.cls().endpoints == self.expected_endpoints


class TestAllowedTrufflehogVendor:
    def test_all_expected_codes_are_returned(self):
        assert AllowedTrufflehogVendor.all_vendor_codes() == [
            "AWS",
            "CircleCI",
            "Datadogtoken",
            "Github",
            "Gitlab",
            "JiraToken",
            "Okta",
            "Slack",
        ]

    def test_all_expected_endpoints_are_returned(self):
        assert AllowedTrufflehogVendor.all_endpoints() == [
            "api.datadoghq.com",
            "sts.us-east-1.amazonaws.com",
            "circleci.com/api/v2/me",
            "api.github.com",
            "gitlab.com",
            "api.atlassian.com",
            "okta.com",
            "slack.com",
        ]


class TestDatadog(BaseVendorTests):
    cls = Datadog
    expected_code = "Datadogtoken"
    expected_endpoints = ["api.datadoghq.com"]


class TestAWS(BaseVendorTests):
    cls = AWS
    expected_code = "AWS"
    expected_endpoints = ["sts.us-east-1.amazonaws.com"]


class TestCircleCI(BaseVendorTests):
    cls = CircleCI
    expected_code = "CircleCI"
    expected_endpoints = ["circleci.com/api/v2/me"]


class TestGithub(BaseVendorTests):
    cls = Github
    expected_code = "Github"
    expected_endpoints = ["api.github.com"]


class TestGitlab(BaseVendorTests):
    cls = Gitlab
    expected_code = "Gitlab"
    expected_endpoints = ["gitlab.com"]


class TestJira(BaseVendorTests):
    cls = Jira
    expected_code = "JiraToken"
    expected_endpoints = ["api.atlassian.com"]


class TestOkta(BaseVendorTests):
    cls = Okta
    expected_code = "Okta"
    expected_endpoints = ["okta.com"]


class TestOSlack(BaseVendorTests):
    cls = Slack
    expected_code = "Slack"
    expected_endpoints = ["slack.com"]
