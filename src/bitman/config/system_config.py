from os.path import join
from typing import Generator

from bitman.config.service_config import ServiceConfig
from . import SYSTEM_CONFIG_PATH


class SystemConfig:
    def __init__(self):
        self._config_directory = SYSTEM_CONFIG_PATH
        self._arch_packages_path = join(self._config_directory, 'arch.packages')
        self._aur_packages_path = join(self._config_directory, 'aur.packages')
        self._services_path = join(self._config_directory, 'services.conf')

    @property
    def user_config_directory(self) -> str:
        return join(self._config_directory, 'user')

    def arch_packages(self) -> Generator[str, None, None]:
        """Yields all Arch packages defined in the bitman config"""
        yield from self._packages(self._arch_packages_path)

    def aur_packages(self) -> Generator[str, None, None]:
        """Yields all AUR packages defined in the bitman config"""
        yield from self._packages(self._aur_packages_path)

    def system_services(self) -> Generator[ServiceConfig, None, None]:
        yield from self._parsed_services('system')

    def user_services(self) -> Generator[ServiceConfig, None, None]:
        yield from self._parsed_services('user')

    def _parsed_services(self, category: str) -> Generator[ServiceConfig, None, None]:
        try:
            with open(self._services_path, 'rt', encoding='utf-8') as config_file:
                found_services_start = False
                for line in config_file:
                    line = line.strip()
                    if line.startswith('#'):
                        continue
                    if not found_services_start and f'[{category}]' in line.lower():
                        found_services_start = True
                        continue
                    if found_services_start and line.startswith('['):
                        break
                    if found_services_start and len(line) > 0:
                        yield self._parsed_service_config(line)
        except IOError:
            yield from []

    def _parsed_service_config(self, line: str) -> ServiceConfig:
        state, name = line.split(' ', 2)
        if state != 'enable' and state != 'disable':
            raise ServiceConfigParseException
        return ServiceConfig(name, state)

    def _packages(self, file_path: str) -> Generator[str, None, None]:
        try:
            with open(file_path, 'rt', encoding='utf-8') as config_file:
                for line in config_file:
                    line = line.strip()
                    if not line.startswith('#') and len(line) > 0:
                        yield line
        except IOError:
            yield from []


class ServiceConfigParseException(BaseException):
    pass
