from abc import ABC, abstractmethod

from logging import getLogger


class Hook(ABC):
    LOG = getLogger()

    def __init__(self, files):
        self.files = files

    @abstractmethod
    def validate_args(self) -> bool:
        pass

    @abstractmethod
    def run(self) -> bool:
        pass
