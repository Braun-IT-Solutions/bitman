from os import path
import subprocess
from subprocess import CompletedProcess
from typing import Literal


class Hook:
    def __init__(self, hook_file_path: str):
        self._file_path = hook_file_path

    def exists(self) -> bool:
        """Returns whether or not the hook exists"""
        return path.isfile(self._file_path)

    def is_installed(self) -> bool:
        """Returns whether or not the hook is installed"""
        result = self._run('installed')
        return result.stdout.startswith('yes')

    def install(self) -> None:
        """Installs the hook"""
        result = self._run('install')

        for line in result.stdout.splitlines():
            print(f'\t{line}')

        for line in result.stderr.splitlines():
            print(f'\t{line}')

        result.check_returncode()

    def remove(self) -> None:
        """Reverts install hook"""
        result = self._run('remove')
        result.check_returncode()

    def _run(self, action: Literal['install', 'remove', 'installed']) -> CompletedProcess[str]:
        result = subprocess.run(
            [self._file_path, action],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        return result
