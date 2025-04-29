
from typing import Literal, NamedTuple


class ServiceConfig(NamedTuple):
    service: str
    desired_state: Literal['enable', 'disable']
