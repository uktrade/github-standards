from abc import ABC, abstractmethod

from logging import getLogger
from typing import List


class Hook(ABC):
    LOG = getLogger()

    def __init__(self, files: List[str] = []):
        self.files = files

    @abstractmethod
    def validate_args(self) -> bool:
        pass

    @abstractmethod
    def run(self) -> bool:
        pass
