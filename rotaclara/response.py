from dataclasses import dataclass, field


@dataclass
class Response:
    data: object
    status: int = 200
    content_type: str = 'application/json; charset=utf-8'
    headers: dict = field(default_factory=dict)
