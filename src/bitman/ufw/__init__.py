import subprocess
from config.ufw_rule import UfwRule, DefaultUfwRule
from typing import Generator, Tuple


class Ufw:
    def __init__(self):
        self._current_verbose = self._verbose_status()
        self._current_numbered_status = self._numbered_status()

    def update_status(self):
        self._current_verbose = self._verbose_status()
        self._current_numbered_status = self._numbered_status()

    def is_enabled(self) -> bool:
        return 'Status: active' in self._current_verbose

    def reload(self) -> None:
        result = subprocess.run(
            ['ufw', 'reload'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()

    def rules(self) -> Generator[UfwRule, None, None]:
        for line in self._current_numbered_status:
            line = line.strip()
            if line.startswith('['):
                yield UfwRule.fromUfwStatus(line)

    def default_rules(self) -> Tuple[DefaultUfwRule, DefaultUfwRule]:
        for line in self._current_verbose:
            line = line.strip()
            if line.startswith('Default: '):
                return DefaultUfwRule.fromUfwStatus(line)
        raise UfwStatusParseException(f"Where default ufw status?")

    def _verbose_status(self) -> str:
        result = subprocess.run(
            ['ufw', 'status', 'verbose'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()
        return result.stdout

    def _numbered_status(self) -> str:
        result = subprocess.run(
            ['ufw', 'status', 'numbered'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()
        return result.stdout


class UfwStatusParseException(BaseException):
    pass
