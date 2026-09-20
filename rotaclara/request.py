from dataclasses import dataclass


@dataclass
class Request:
    query: dict
    data: dict
    client: str
    token: str
    user: dict | None = None
