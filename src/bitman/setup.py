
import getpass
import os
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

        if not self._bind_mount_exists(user_local_bitman_directory):
            print("bindfs already exists, skipping")
            self._extend_fstab(bitman_user_directory, user_local_bitman_directory, username)
            self._mount_bindfs(bitman_user_directory, user_local_bitman_directory, username)

        self._create_symlinks(user_local_bitman_directory, user_home)

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

    def _bind_mount_exists(self, user_bitman_directory: str) -> bool:
        result = subprocess.run(
            ['mount'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()

        return user_bitman_directory in result.stdout

    def _mount_bindfs(self, system_bitman_directory: str, user_bitman_directory: str, username: str) -> None:
        result = subprocess.run(
            ['sudo', 'bindfs', '-u', username, '-g', username,
                system_bitman_directory, user_bitman_directory],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()

    def _create_symlinks(self, user_bitman_directory: str, user_home_directory: str) -> None:
        symlinks = self._system_config.symlinks()
        for symlink in symlinks:
            symlink = symlink.removesuffix('/')

            target_path = join(user_home_directory, symlink)
            if os.path.islink(target_path):
                print(f'Skipping {symlink}...')
                continue

            print(f'Symlinking {symlink}...')
            os.symlink(join(user_bitman_directory, symlink), target_path)
