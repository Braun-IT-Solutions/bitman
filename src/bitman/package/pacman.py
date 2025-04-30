import subprocess
from typing import Generator

from bitman.package.package_manager import PackageManager


class Pacman(PackageManager):
    def install_packages(self, packages):
        result = subprocess.run(
            ['sudo', 'pacman', '-S', '--asexplicit', '--needed', '--noconfirm', *packages],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()

    def remove_packages(self, packages):
        result = subprocess.run(
            ['sudo', 'pacman', '-R', '--noconfirm', *packages],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()

    def explicitly_installed_packages(self) -> Generator[str, None, None]:
        """Yields all explicitly installed packages (packages which weren't installed as a dependency)"""
        result = subprocess.run(
            ['pacman', '-Qe'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        if result.returncode != 0 and result.stderr:
            result.check_returncode()
        for line in result.stdout.splitlines():
            yield line.split(' ', 1)[0]

    def foreign_installed_packages(self) -> Generator[str, None, None]:
        """Yields all foreign installed packages (e. g. those from the AUR)"""
        result = subprocess.run(
            ['pacman', '-Qm'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        if result.returncode != 0 and result.stderr:
            result.check_returncode()
        for line in result.stdout.splitlines():
            yield line.split(' ', 1)[0]

    def package_installed(self, package: str) -> bool:
        """Returns whether or not a certain package is installed"""
        result = subprocess.run(
            ['pacman', '-Q', package],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        return result.returncode == 0
