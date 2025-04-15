from argparse import Namespace
from rich.console import Console
from bitman.config.system_config import SystemConfig
from bitman.pacman import Pacman
from bitman.sync import Sync


class Bitman:
    def __init__(self):
        self._system_config = SystemConfig()
        self._pacman = Pacman()
        self._sync = Sync(self._system_config, self._pacman)
        self._console = Console()

    def sync(self, args: Namespace):
        """Processes bitman sync command"""
        if args.status:
            status = self._sync.status()
            self._console.print('Additional', style='bold yellow')
            self._console.print(*['[bold]·[/bold] ' + line for line in status.additional], sep='\n')

            self._console.print('\nMissing', style='bold red')
            self._console.print(
                *['[bold]·[/bold] ' + line for line in status.missing_arch], sep='\n', highlight=False)
            self._console.print(*['[bold]·[/bold] ' + line +
                                ' (AUR)' for line in status.missing_aur], sep='\n', highlight=False)
        else:
            print('Not implemented')
