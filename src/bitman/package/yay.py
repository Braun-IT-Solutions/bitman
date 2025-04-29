import subprocess
from rich.console import Console
from bitman.package.package_manager import PackageManager
from bitman.package.pacman import Pacman


class Yay(PackageManager):
    def __init__(self):
        self._console = Console()

    def install_packages(self, packages):
        if not self._is_installed():
            self._console.print(
                '[red]Package manager [bold]yay[/bold] is currently not installed[/red]')
            # TODO: install yay via git clone & makepkg
            raise YayNotInstalledException()

        result = subprocess.run(
            ['yay', '-S', '--noconfirm', '--needed', *packages],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()

        result = subprocess.run(
            ['pacman', '-D', '--asexplicit', *packages],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()

    def _is_installed(self) -> bool:
        pacman = Pacman()
        installed_packages = pacman.foreign_installed_packages()
        return 'yay' in installed_packages


class YayNotInstalledException(BaseException):
    pass
