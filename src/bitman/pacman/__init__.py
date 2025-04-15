import re
import subprocess
from typing import Generator


class Pacman:
    def explicitly_installed_packages(self) -> Generator[str, None, None]:
        """Yields all explicitly installed packages (packages which weren't installed as a dependency)"""
        result = subprocess.run(
            ['pacman', '-Qe'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()
        for line in result.stdout.splitlines():
            yield re.search("([^ ]+)", line).group(1)

    def foreign_installed_packages(self) -> Generator[str, None, None]:
        """Yields all foreign installed packages (e. g. those from the AUR)"""
        result = subprocess.run(
            ['pacman', '-Qm'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()
        for line in result.stdout.splitlines():
            yield re.search("([^ ]+)", line).group(1)
