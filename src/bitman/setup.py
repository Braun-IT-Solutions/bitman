
import getpass
from pathlib import Path
import subprocess
from bitman.config.system_config import SystemConfig
from os.path import join

from bitman.service import Systemd


class Setup:
    def __init__(self, system_config: SystemConfig, systemd: Systemd):
        self._system_config = system_config
        self._systemd = systemd

    def run(self) -> None:
        bitman_user_directory = self._system_config.user_config_directory
        user_home = Path.home()
        user_local_bitman_directory = join(user_home, '.bitman')
        username = getpass.getuser()

        print("Setup")
        print(f"Bitman user directory: {bitman_user_directory}")
        print(f"User home: {user_home}")
        print(f"User local bitman directory: {user_local_bitman_directory}")
        print(f"Username: {username}")

        self._extend_fstab(bitman_user_directory, user_local_bitman_directory, username)

    def _extend_fstab(self, system_bitman_directory: str, user_bitman_directory: str, username: str) -> None:
        result = subprocess.run(
            f'sudo sh -c "echo \'{system_bitman_directory}\t{user_bitman_directory}\tfuse.bindfs\tforce-user={username},force-group={username}\t0\t2\' >> /etc/fstab"',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False,
            shell=True,
            executable='/bin/bash'
        )
        result.check_returncode()

        self._systemd.reload_daemon()

    def _mount_bindfs(self) -> None:
        pass

    def _create_symlinks(self) -> None:
        pass
