from typing import NamedTuple
from rich.console import Console

from bitman.service import Systemd


class ServiceSyncStatus(NamedTuple):
    system_to_disable: list[str]
    system_to_enable: list[str]
    user_to_disable: list[str]
    user_to_enable: list[str]


class ServicesSync:
    def __init__(self, status: ServiceSyncStatus, console: Console):
        self._status = status
        self._console = console

    def print_summary(self) -> None:
        status = self._status

        if len(status.system_to_disable) == 0 and len(status.system_to_enable) == 0 and len(status.user_to_disable) == 0 and len(status.user_to_enable) == 0:
            self._console.print('Everything in sync, nothing to do', style='bold green')
            return

        if len(status.system_to_enable) > 0:
            self._console.print(
                'The following system services will be [bold]enabled[/bold]:', style='yellow')
            self._console.print(
                *['[bold]·[/bold] ' + service for service in status.system_to_enable], sep='\n', highlight=False)
            self._console.line()

        if len(status.system_to_disable) > 0:
            self._console.print(
                'The following system services will be [bold]disabled[/bold]:', style='yellow')
            self._console.print(
                *['[bold]·[/bold] ' + service for service in status.system_to_disable], sep='\n', highlight=False)
            self._console.line()

        if len(status.user_to_enable) > 0:
            self._console.print(
                'The following user services will be [bold]enabled[/bold]:', style='yellow')
            self._console.print(
                *['[bold]·[/bold] ' + service for service in status.user_to_enable], sep='\n', highlight=False)
            self._console.line()

        if len(status.user_to_disable) > 0:
            self._console.print(
                'The following user services will be [bold]disabled[/bold]:', style='yellow')
            self._console.print(
                *['[bold]·[/bold] ' + service for service in status.user_to_disable], sep='\n', highlight=False)
            self._console.line()

    def run(self, systemd: Systemd) -> None:
        status = self._status

        for service in status.system_to_enable:
            self._console.print(f'Enabling {service}...', end='')
            systemd.enable_service(service)
            self._console.print(' Done!')

        for service in status.user_to_enable:
            self._console.print(f'Enabling {service}...', end='')
            systemd.enable_service(service, user=True)
            self._console.print(' Done!')

        for service in status.system_to_disable:
            self._console.print(f'Disbling {service}...', end='')
            systemd.disable_service(service)
            self._console.print(' Done!')

        for service in status.user_to_disable:
            self._console.print(f'Disbling {service}...', end='')
            systemd.disable_service(service, user=True)
            self._console.print(' Done!')
