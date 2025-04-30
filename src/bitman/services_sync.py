from typing import NamedTuple
from rich.console import Console

from bitman.config.system_config import SystemConfig
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

    def print_status(self, systemd: Systemd, system_config: SystemConfig) -> None:
        """Prints the status of the currently configured services"""
        services = system_config.system_services()
        self._console.print('\nSystem Services:', style='bold white')
        for service in services:
            service_enabled = systemd.service_enabled(service.service)
            running = systemd.service_running(service.service)
            should_be_enabled = service.desired_state == 'enable'
            self._console.print(
                f'[bold]{'[green]✔[/green]' if service_enabled == should_be_enabled else '[red]❌[/red]'}[/bold] {service.service} is [bold]{'enabled' if service_enabled else 'disabled'}[/bold] {'and [bold]running[/bold]' if running else 'but [bold]not running[/bold]'} (should be {service.desired_state}d)')

        user_services = system_config.user_services()
        self._console.print('\nUser Services:', style='bold white')
        for service in user_services:
            service_enabled = systemd.service_enabled(service.service, user=True)
            running = systemd.service_running(service.service, user=True)
            should_be_enabled = service.desired_state == 'enable'
            self._console.print(
                f'[bold]{'[green]✔[/green]' if service_enabled == should_be_enabled else '[red]❌[/red]'}[/bold] {service.service} is [bold]{'enabled' if service_enabled else 'disabled'}[/bold] {'and [bold]running[/bold]' if running else 'but [bold]not running[/bold]'} (should be {service.desired_state}d)')

    def print_summary(self) -> None:
        """Prints the pre-sync summary of the changes that will be made"""
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
        """Enables and disables services to make them match the configuration"""
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
