from os.path import join
from typing import Callable, NamedTuple

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TaskID
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

from bitman.hook import Hook
from bitman.package.pacman import Pacman
from bitman.package.yay import Yay, YayNotInstalledException


class TaskInfo(NamedTuple):
    task: TaskID
    command: Callable[[None], None]


class PackageSyncStatus(NamedTuple):
    additional: list[str]
    missing_arch: list[str]
    missing_aur: list[str]
    installed: list[str]


class PackageSync:
    def __init__(self, status: PackageSyncStatus, console: Console, hooks_path: str):
        self._status = status
        self._console = console
        self._hooks_path = hooks_path

    def print_summary(self) -> None:
        """Prints which changes will be made to the installed packages if sync is run"""
        status = self._status
        console = self._console

        if len(status.additional) == 0 and len(status.missing_aur) == 0 and len(status.missing_arch) == 0:
            console.print('All packages are in sync, nothing to do', style='green')

        if len(status.missing_arch) > 0 or len(status.missing_aur) > 0:
            console.print('The following packages will be installed:', style='yellow')

            if len(status.missing_arch) > 0:
                console.print(
                    *['[bold]·[/bold] ' + line for line in status.missing_arch], sep='\n', highlight=False)

            if len(status.missing_aur) > 0:
                console.print(*['[bold]·[/bold] ' + line +
                                ' (AUR)' for line in status.missing_aur], sep='\n', highlight=False)
            console.line()

        if len(status.additional) > 0:
            console.print('The following packages will be removed:', style='red')
            console.print(
                *['[bold]·[/bold] ' + line for line in status.additional], sep='\n')
            console.line()

    def run(self, pacman: Pacman, yay: Yay) -> None:
        """Executes package sync"""
        self._run_installs(pacman, yay)
        self._run_hooks()

    def _run_installs(self, pacman: Pacman, yay: Yay) -> None:
        progress = Progress(
            "{task.description}",
            SpinnerColumn(finished_text='[green]✔')
        )

        status = self._status
        tasks: list[TaskInfo] = []

        if len(status.additional) > 0:
            remove_task = progress.add_task('[red]Removing additional packages', total=1)
            tasks.append(
                TaskInfo(remove_task, lambda: pacman.remove_packages(status.additional)))

        if len(status.missing_arch) > 0:
            arch_task = progress.add_task('[yellow]Installing packages', total=1)
            tasks.append(
                TaskInfo(arch_task, lambda: pacman.install_packages(status.missing_arch)))

        if len(status.missing_aur) > 0:
            aur_task = progress.add_task('[yellow]Installing packages (AUR)', total=1)
            tasks.append(TaskInfo(aur_task, lambda: yay.install_packages(status.missing_aur)))

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

    def _run_hooks(self) -> None:
        status = self._status
        hooks_path = self._hooks_path
        console = self._console

        for package in status.additional:
            hook = Hook(join(hooks_path, package))
            if not hook.exists():
                continue

            if not hook.is_installed():
                console.print(f'Skipping remove hook for {package} (was not installed)')
                continue

            console.print(f'Running remove hook for {package}...')
            hook.remove()

        for package in status.installed:
            hook = Hook(join(hooks_path, package))
            if not hook.exists():
                continue

            if hook.is_installed():
                console.print(f'Skipping install hook for {package} (was already installed)')
                continue

            console.print(f'Running install hook for {package}...')
            hook.install()
