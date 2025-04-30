from argparse import Namespace
from os import path
from rich.console import Console
from rich.prompt import Prompt

from bitman.config import SYSTEM_CONFIG_PATH
from bitman.config.system_config import SystemConfig
from bitman.git import Git
from bitman.package.pacman import Pacman
from bitman.package.yay import Yay
from bitman.package_sync import PackageSync
from bitman.service import Systemd
from bitman.services_sync import ServicesSync
from bitman.setup import Setup
from bitman.sync import Sync, SyncScope, PackageSyncStatus
from bitman.ufw import Ufw


class Bitman:
    def __init__(self):
        self._system_config = SystemConfig()
        self._pacman = Pacman()
        self._ufw = Ufw()
        self._yay = Yay()
        self._systemd = Systemd()
        self._sync = Sync(self._system_config, self._pacman, self._yay, self._systemd, self._ufw)
        self._console = Console()

    def init(self, _args: Namespace) -> None:
        """Initializes bitman on the system (pulls config repo to /etc/bitman)"""
        pacman = self._pacman
        console = self._console
        bitman_path = SYSTEM_CONFIG_PATH

        if path.exists(bitman_path):
            console.print(
                f'The directory [bold]{bitman_path}[/bold] already exists, aborting', style='red')
            return

        if not pacman.package_installed('git'):
            console.print(
                '[bold]git[/bold] is currently not installed, but it is required for this step')
            answer = Prompt.ask('Do you want to install git?', choices=[
                'yes', 'no'], default='yes', case_sensitive=False)
            if answer != 'yes':
                return

            self._pacman.install_packages(['git'])

        config_repo = ''

        while len(config_repo) == 0:
            config_repo = Prompt.ask('Please enter the git link of your config repo')
            config_repo = config_repo.strip()

        git = Git()

        console.print('Cloning repository...')
        repo = git.clone(config_repo, bitman_path)

        branches = repo.branches()
        console.print('Available branches:', style='yellow')
        console.print(
            *[f'[bold]·[/bold] {branch}' for branch in branches], sep='\n')

        selected_branch = Prompt.ask('Which branch should be used? (type its name)',
                                     choices=branches, show_choices=False)

        if selected_branch != repo.active_branch():
            console.print(f'Switching branch to {selected_branch}...')
            repo.change_branch(selected_branch)

            console.print('Pulling...')
            repo.pull()

        console.print('You\'re ready to go!', style='bold green')

    def sync(self, args: Namespace) -> None:
        """Processes bitman sync command"""

        scope = SyncScope(args)
        if args.status:
            if scope.packages:
                status = self._sync.package_status()
                sync = PackageSync(status, self._console)
                sync.print_status()

            if scope.services:
                status = self._sync.service_status()
                sync = ServicesSync(status, self._console)
                sync.print_status(self._systemd, self._system_config)

            if scope.ufw:
                self._print_ufw_status()
        else:
            self._sync.run(scope)

    def _print_ufw_status(self) -> None:
        self._sync.print_ufw_status()

    def install(self, args: Namespace) -> None:
        """Processes bitman user install command"""
        print("Not implemented", args)

    def setup(self, args: Namespace) -> None:
        """Setup user files"""
        setup = Setup(self._system_config, self._systemd)
        setup.run()
