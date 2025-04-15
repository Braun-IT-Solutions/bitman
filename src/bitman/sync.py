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


class SyncStatus(NamedTuple):
    additional: list[str]
    missing_arch: list[str]
    missing_aur: list[str]


class TaskInfo(NamedTuple):
    task: TaskID
    command: Callable[[None], None]


class Sync:
    def __init__(self, system_config: SystemConfig, pacman: Pacman, yay: Yay):
        self._system_config = system_config
        self._pacman = pacman
        self._yay = yay
        self._console = Console()

    def status(self) -> SyncStatus:
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

        return SyncStatus(additional_packages, missing_arch_packages, missing_aur_packages)

    def run(self) -> None:
        """Runs a sync which will remove additional and install missing packages"""
        status = self.status()

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
