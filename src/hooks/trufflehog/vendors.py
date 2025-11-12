import itertools

from abc import ABC, abstractmethod
from typing import List

from src.hooks.config import LOGGER


logger = LOGGER


class AllowedTrufflehogVendor(ABC):
    @property
    @abstractmethod
    def code(self) -> str:
        pass

    @property
    @abstractmethod
    def endpoints(self) -> list[str]:
        pass

    @staticmethod
    def all_endpoints() -> List[str]:
        """
        Get a list of all endpoints used by the configured trufflehog vendors

        Returns:
            List[str]: A list of endpoints
        """

        return list(itertools.chain.from_iterable([cls().endpoints for cls in AllowedTrufflehogVendor.__subclasses__()]))

    @staticmethod
    def all_vendor_codes() -> List[str]:
        """
        Get a list of all configured trufflehog vendor codes

        Returns:
            List[str]: A list of trufflehog codes
        """
        codes = [cls().code for cls in AllowedTrufflehogVendor.__subclasses__()]
        codes.sort()
        return codes

    @staticmethod
    def all_vendor_codes_as_str() -> str:
        """
        Get a list of all configured trufflehog vendor codes in a comma separated string

        Returns:
            str: A str of trufflehog codes
        """
        return ",".join(AllowedTrufflehogVendor.all_vendor_codes())


class Datadog(AllowedTrufflehogVendor):
    @property
    def code(self) -> str:
        return "Datadogtoken"

    @property
    def endpoints(self) -> list[str]:
        return ["api.datadoghq.com"]


class AWS(AllowedTrufflehogVendor):
    @property
    def code(self) -> str:
        return "AWS"

    @property
    def endpoints(self) -> list[str]:
        return [
            "sts.us-east-1.amazonaws.com",
            "sns.us-east-1.amazonaws.com",
        ]


class CircleCI(AllowedTrufflehogVendor):
    @property
    def code(self) -> str:
        return "CircleCI"

    @property
    def endpoints(self) -> list[str]:
        return [
            "circleci.com/api/v2/me",
        ]


class Github(AllowedTrufflehogVendor):
    @property
    def code(self) -> str:
        return "Github"

    @property
    def endpoints(self) -> list[str]:
        return ["api.github.com"]


class Gitlab(AllowedTrufflehogVendor):
    @property
    def code(self) -> str:
        return "Gitlab"

    @property
    def endpoints(self) -> list[str]:
        return ["gitlab.com"]


class Jira(AllowedTrufflehogVendor):
    @property
    def code(self) -> str:
        return "JiraToken"

    @property
    def endpoints(self) -> list[str]:
        return ["api.atlassian.com"]


class Okta(AllowedTrufflehogVendor):
    @property
    def code(self) -> str:
        return "Okta"

    @property
    def endpoints(self) -> list[str]:
        return ["okta.com"]


class Slack(AllowedTrufflehogVendor):
    @property
    def code(self) -> str:
        return "Slack"

    @property
    def endpoints(self) -> list[str]:
        return ["slack.com"]
