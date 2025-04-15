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
            print(*status.additional, sep='\n\t')

            print('\nMissing from Arch Repository:')
            print(*status.missing_arch, sep='\n\t')

            print('\nMissing from AUR:')
            print(*status.missing_aur, sep='\n\t')
        else:
            print('Not implemented')
