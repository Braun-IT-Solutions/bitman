from argparse import Namespace
import time
from typing import Callable, NamedTuple
from rich.prompt import Prompt
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TaskID
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from bitman.config.system_config import SystemConfig
from bitman.package.pacman import Pacman
from bitman.package.yay import Yay, YayNotInstalledException
from bitman.service import Systemd


class PackageSyncStatus(NamedTuple):
    additional: list[str]
    missing_arch: list[str]
    missing_aur: list[str]


class ServiceSyncStatus(NamedTuple):
    system_to_disable: list[str]
    system_to_enable: list[str]
    user_to_disable: list[str]
    user_to_enable: list[str]


class TaskInfo(NamedTuple):
    task: TaskID
    command: Callable[[None], None]


class SyncScope():
    def __init__(self, args: Namespace):
        all_enabled = not args.packages and not args.services
        self._packages = args.packages or all_enabled
        self._services = args.services or all_enabled

    @property
    def packages(self) -> bool:
        return self._packages

    @property
    def services(self) -> bool:
        return self._services


class Sync:
    def __init__(self, system_config: SystemConfig, pacman: Pacman, yay: Yay, systemd: Systemd):
        self._system_config = system_config
        self._pacman = pacman
        self._yay = yay
        self._systemd = systemd
        self._console = Console()

    def package_status(self) -> PackageSyncStatus:
        """
        Returns which additional packages are installed and which are missing compared to the ones
        configured using bitman
        """
        required_arch_packages = set(self._system_config.arch_packages())
        required_aur_packages = set(self._system_config.aur_packages())
        installed_arch_packages = set(self._pacman.explicitly_installed_packages())
        installed_aur_packages = set(self._pacman.foreign_installed_packages())

        missing_arch_packages = required_arch_packages.difference(installed_arch_packages)
        missing_aur_packages = required_aur_packages.difference(installed_aur_packages)
        additional_packages = installed_arch_packages.union(installed_aur_packages).difference(
            required_arch_packages.union(required_aur_packages)
        )

        return PackageSyncStatus(additional_packages, missing_arch_packages, missing_aur_packages)

    def service_status(self) -> ServiceSyncStatus:
        """
        Returns which services are enabled, but shouldn't be and vice-versa
        """
        wanted_services = list(self._system_config.system_services())
        wanted_enabled_system_services = [
            config.service for config in wanted_services if config.desired_state == 'enable']
        wanted_disabled_system_services = [
            config.service for config in wanted_services if config.desired_state == 'disable']

        system_services_to_enable = [
            service for service in wanted_enabled_system_services if not self._systemd.service_enabled(service)]
        system_services_to_disable = [
            service for service in wanted_disabled_system_services if self._systemd.service_enabled(service)]

        wanted_user_services = list(self._system_config.user_services())
        wanted_enabled_user_services = [
            config.service for config in wanted_user_services if config.desired_state == 'enable']
        wanted_disabled_user_services = [
            config.service for config in wanted_user_services if config.desired_state == 'disable']

        user_services_to_enable = [
            service for service in wanted_enabled_user_services if not self._systemd.service_enabled(service, user=True)]
        user_services_to_disable = [
            service for service in wanted_disabled_user_services if self._systemd.service_enabled(service, user=True)]

        return ServiceSyncStatus(system_services_to_disable, system_services_to_enable, user_services_to_disable, user_services_to_enable)

    def run(self, scope: SyncScope) -> None:
        """Runs a sync which will remove additional and install missing packages"""

        if scope.packages:
            self._run_packages()

        if scope.services:
            self._run_services()

    def _run_packages(self) -> None:
        status = self.package_status()

        if len(status.additional) == 0 and len(status.missing_aur) == 0 and len(status.missing_arch) == 0:
            self._console.print('All packages are in sync, nothing to do', style='green')

        if len(status.missing_arch) > 0 or len(status.missing_aur) > 0:
            self._console.print('The following packages will be installed:', style='yellow')

            if len(status.missing_arch) > 0:
                self._console.print(
                    *['[bold]·[/bold] ' + line for line in status.missing_arch], sep='\n', highlight=False)

            if len(status.missing_aur) > 0:
                self._console.print(*['[bold]·[/bold] ' + line +
                                    ' (AUR)' for line in status.missing_aur], sep='\n', highlight=False)
            self._console.line()

        if len(status.additional) > 0:
            self._console.print('The following packages will be removed:', style='red')
            self._console.print(
                *['[bold]·[/bold] ' + line for line in status.additional], sep='\n')
            self._console.line()

        answer = Prompt.ask('Do you want to continue?', choices=[
                            'yes', 'no'], default='yes', case_sensitive=False)
        if answer != 'yes':
            return

        progress = Progress(
            "{task.description}",
            SpinnerColumn(finished_text='[green]✔')
        )

        tasks: list[TaskInfo] = []

        if len(status.additional) > 0:
            remove_task = progress.add_task('[red]Removing additional packages', total=1)
            tasks.append(
                TaskInfo(remove_task, lambda: self._pacman.remove_packages(status.additional)))

        if len(status.missing_arch) > 0:
            arch_task = progress.add_task('[yellow]Installing packages', total=1)
            tasks.append(
                TaskInfo(arch_task, lambda: self._pacman.install_packages(status.missing_arch)))

        if len(status.missing_aur) > 0:
            aur_task = progress.add_task('[yellow]Installing packages (AUR)', total=1)
            tasks.append(TaskInfo(aur_task, lambda: self._yay.install_packages(status.missing_aur)))

        progress_table = Table.grid()
        progress_table.add_row(
            Panel.fit(progress, title='[b]Tasks', border_style='red', padding=(1, 2))
        )

        try:
            with Live(progress_table, refresh_per_second=10):
                for task in tasks:
                    task.command()
                    progress.advance(task.task)
        except YayNotInstalledException:
            self._console.print(
                "Could not install AUR packages, [bold]yay[/bold] is not installed", style='red')

    def _run_services(self) -> None:
        status = self.service_status()
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

        answer = Prompt.ask('Do you want to continue?', choices=[
                            'yes', 'no'], default='yes', case_sensitive=False)
        if answer != 'yes':
            return

        for service in status.system_to_enable:
            self._console.print(f'Enabling {service}...', end='')
            self._systemd.enable_service(service)
            self._console.print(' Done!')

        for service in status.user_to_enable:
            self._console.print(f'Enabling {service}...', end='')
            self._systemd.enable_service(service, user=True)
            self._console.print(' Done!')

        for service in status.system_to_disable:
            self._console.print(f'Disbling {service}...', end='')
            self._systemd.disable_service(service)
            self._console.print(' Done!')

        for service in status.user_to_disable:
            self._console.print(f'Disbling {service}...', end='')
            self._systemd.disable_service(service, user=True)
            self._console.print(' Done!')
