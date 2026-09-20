import re
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Endpoint:
    method: str
    pattern: str
    handler: Callable
    requires_authentication: bool = True

    def match(self, method, path):
        if method != self.method:
            return None
        match = re.fullmatch(self.pattern, path)
        if match is None:
            return None
        return {name: int(value) for name, value in match.groupdict().items()}
