from typing import NamedTuple
from bitman.config.system_config import SystemConfig
from bitman.pacman import Pacman


class SyncStatus(NamedTuple):
    additional: list[str]
    missing_arch: list[str]
    missing_aur: list[str]


class Sync:
    def __init__(self, system_config: SystemConfig, pacman: Pacman):
        self._system_config = system_config
        self._pacman = pacman

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
