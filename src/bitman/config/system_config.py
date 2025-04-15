from os.path import join
from typing import Generator
from . import SYSTEM_CONFIG_PATH


class SystemConfig:
    def __init__(self):
        self._config_directory = SYSTEM_CONFIG_PATH
        self._arch_packages_path = join(self._config_directory, 'arch.packages')
        self._aur_packages_path = join(self._config_directory, 'aur.packages')

    def arch_packages(self) -> Generator[str, None, None]:
        """Yields all Arch packages defined in the bitman config"""
        yield from self._packages(self._arch_packages_path)

    def aur_packages(self) -> Generator[str, None, None]:
        """Yields all AUR packages defined in the bitman config"""
        yield from self._packages(self._aur_packages_path)

    def _packages(self, file_path: str) -> Generator[str, None, None]:
        try:
            with open(file_path, 'rt', encoding='utf-8') as config_file:
                for line in config_file:
                    line = line.strip()
                    if not line.startswith('#') and len(line) > 0:
                        yield line
        except IOError:
            yield from []
