from os.path import join
from typing import Generator

from bitman.config.service_config import ServiceConfig
from . import SYSTEM_CONFIG_PATH
from .ufw_rule import UfwRule, DefaultUfwRule


class SystemConfig:
    def __init__(self):
        self._config_directory = SYSTEM_CONFIG_PATH
        self._arch_packages_path = join(self._config_directory, 'arch.packages')
        self._aur_packages_path = join(self._config_directory, 'aur.packages')
        self._services_path = join(self._config_directory, 'services.conf')
        self._symlinks_file_path = join(self._config_directory, 'user', 'symlinks')
        self._ufw_rules_path = join(self._config_directory, 'ufw.conf')
        self._hooks_directory = join(self._config_directory, 'hooks')

    @property
    def user_config_directory(self) -> str:
        """Returns path to bitman user files directory"""
        return join(self._config_directory, 'user')

    def arch_packages(self) -> Generator[str, None, None]:
        """Yields all Arch packages defined in the bitman config"""
        yield from self._packages(self._arch_packages_path)

    def aur_packages(self) -> Generator[str, None, None]:
        """Yields all AUR packages defined in the bitman config"""
        yield from self._packages(self._aur_packages_path)

    def system_services(self) -> Generator[ServiceConfig, None, None]:
        """Returns list of configured system services"""
        yield from self._parsed_services('system')

    def user_services(self) -> Generator[ServiceConfig, None, None]:
        """Returns list of configured user services"""
        yield from self._parsed_services('user')

    def symlinks(self) -> Generator[str, None, None]:
        """Returns list of configured symlinks for user files"""
        try:
            with open(self._symlinks_file_path, 'rt', encoding='utf-8') as config_file:
                for line in config_file:
                    line = line.strip()
                    if not line.startswith('#') and len(line) > 0:
                        yield line
        except IOError:
            yield from []

    def ufw_rules(self) -> Generator[UfwRule, None, None]:
        """Returns list of configured UFW rules"""
        yield from self._parsed_ufw_rules()

    def default_ufw_rules(self) -> Generator[UfwRule, None, None]:
        """Returns list of configured default UFW rules"""
        yield from self._parsed_default_ufw_rules()

    def hooks_directory(self) -> str:
        """Returns path to hooks directory"""
        return self._hooks_directory

    def _parsed_ufw_rules(self):
        with open(self._ufw_rules_path, 'rt', encoding='utf-8') as config_file:
            is_rule_block = False
            for line in config_file:
                line = line.strip()
                if line.startswith('#') or line == '':
                    continue
                if not is_rule_block and '[rules]' in line.lower():
                    is_rule_block = True
                    continue
                if is_rule_block and line.startswith('['):
                    break
                if is_rule_block:
                    yield UfwRule.fromBitmanConfig(line)

    def _parsed_default_ufw_rules(self) -> Generator[DefaultUfwRule, None, None]:
        with open(self._ufw_rules_path, 'rt', encoding='utf-8') as config_file:
            is_rule_block = False
            for line in config_file:
                line = line.strip()
                if line.startswith('#') or line == '':
                    continue
                if not is_rule_block and '[default]' in line.lower():
                    is_rule_block = True
                    continue
                if is_rule_block and line.startswith('['):
                    break
                if is_rule_block:
                    yield DefaultUfwRule.fromBitmanConfig(line)

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
