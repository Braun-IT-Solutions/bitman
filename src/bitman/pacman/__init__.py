import re
import subprocess


class Pacman:
    def explicitly_installed_packages(self):
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
