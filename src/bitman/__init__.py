from argparse import Namespace
from bitman.config.system_config import SystemConfig
from bitman.pacman import Pacman
from bitman.sync import Sync


class Bitman:
    def __init__(self):
        self._system_config = SystemConfig()
        self._pacman = Pacman()
        self._sync = Sync(self._system_config, self._pacman)

    def sync(self, args: Namespace):
        """Processes bitman sync command"""
        if args.status:
            status = self._sync.status()
            print('Additional:')
            print(*['\t' + line for line in status.additional], sep='\n')

            print('\nMissing from Arch Repository:')
            print(*['\t' + line for line in status.missing_arch], sep='\n')

            print('\nMissing from AUR:')
            print(*['\t' + line for line in status.missing_aur], sep='\n')
        else:
            print('Not implemented')
