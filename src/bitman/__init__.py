from argparse import Namespace
from rich.console import Console
from bitman.config.system_config import SystemConfig
from bitman.package.pacman import Pacman
from bitman.package.yay import Yay
from bitman.sync import Sync


class Bitman:
    def __init__(self):
        self._system_config = SystemConfig()
        self._pacman = Pacman()
        self._yay = Yay()
        self._sync = Sync(self._system_config, self._pacman, self._yay)
        self._console = Console()

    def sync(self, args: Namespace) -> None:
        """Processes bitman sync command"""
        if args.status:
            status = self._sync.status()

            if len(status.additional) == 0 and len(status.missing_aur) == 0 and len(status.missing_arch) == 0:
                self._console.print('All packages are in sync', style='green')
                return

            self._console.print('Additional', style='bold yellow')
            if len(status.additional) > 0:
                self._console.print(
                    *['[bold]·[/bold] ' + line for line in status.additional], sep='\n')

            self._console.print('\nMissing', style='bold red')
            if len(status.missing_arch) > 0:
                self._console.print(
                    *['[bold]·[/bold] ' + line for line in status.missing_arch], sep='\n', highlight=False)
            if len(status.missing_aur) > 0:
                self._console.print(*['[bold]·[/bold] ' + line +
                                      ' (AUR)' for line in status.missing_aur], sep='\n', highlight=False)
        else:
            self._sync.run()

    def install(self, args: Namespace) -> None:
        """Processes bitman user install command"""
        print("Not implemented", args)
