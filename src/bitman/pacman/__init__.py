import subprocess
from typing import Generator


class Pacman:
    def install_packages(self, packages: list[str]) -> None:
        """Installs the given packages"""
        result = subprocess.run(
            ['pacman', '-S', '--noconfirm', *packages],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()

    def remove_packages(self, packages: list[str]) -> None:
        """Removes the given packages"""
        result = subprocess.run(
            ['pacman', '-R', '--noconfirm', *packages],
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
