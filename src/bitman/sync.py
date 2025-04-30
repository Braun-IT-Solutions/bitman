from argparse import Namespace
from rich.prompt import Prompt
from rich.console import Console
from bitman.config.system_config import SystemConfig
from bitman.package.pacman import Pacman
from bitman.package.yay import Yay
from bitman.package_sync import PackageSync, PackageSyncStatus
from bitman.service import Systemd
from bitman.services_sync import ServiceSyncStatus, ServicesSync
from bitman.ufw import Ufw
from bitman.ufw_sync import UfwSync


class SyncScope():
    def __init__(self, args: Namespace):
        all_enabled = not args.packages \
            and not args.services\
            and not args.ufw
        self._packages = args.packages or all_enabled
        self._services = args.services or all_enabled
        self._ufw = args.ufw or all_enabled

    @property
    def packages(self) -> bool:
        return self._packages

    @property
    def services(self) -> bool:
        return self._services

    @property
    def ufw(self) -> bool:
        return self._ufw


class Sync:
    def __init__(self, system_config: SystemConfig, pacman: Pacman, yay: Yay, systemd: Systemd, ufw: Ufw):
        self._system_config = system_config
        self._pacman = pacman
        self._yay = yay
        self._systemd = systemd
        self._ufw = ufw
        self._console = Console()

    def package_status(self) -> PackageSyncStatus:
        """
        Returns which additional packages are installed and which are missing compared to the ones
        configured using bitman
        """
        required_arch_packages = set(self._system_config.arch_packages())
        required_aur_packages = set(self._system_config.aur_packages())
        installed_arch_packages = set(self._pacman.explicitly_installed_packages())
        installed_aur_packages = set(self._pacman.foreign_installed_packages())

        missing_arch_packages = required_arch_packages.difference(installed_arch_packages)
        missing_aur_packages = required_aur_packages.difference(installed_aur_packages)
        additional_packages = installed_arch_packages.union(installed_aur_packages).difference(
            required_arch_packages.union(required_aur_packages)
        )

        return PackageSyncStatus(list(additional_packages), list(missing_arch_packages), list(missing_aur_packages), list(required_arch_packages) + list(required_aur_packages))

    def service_status(self) -> ServiceSyncStatus:
        """
        Returns which services are enabled, but shouldn't be and vice-versa
        """
        wanted_services = list(self._system_config.system_services())
        wanted_enabled_system_services = [
            config.service for config in wanted_services if config.desired_state == 'enable']
        wanted_disabled_system_services = [
            config.service for config in wanted_services if config.desired_state == 'disable']

        system_services_to_enable = [
            service for service in wanted_enabled_system_services if not self._systemd.service_enabled(service)]
        system_services_to_disable = [
            service for service in wanted_disabled_system_services if self._systemd.service_enabled(service)]

        wanted_user_services = list(self._system_config.user_services())
        wanted_enabled_user_services = [
            config.service for config in wanted_user_services if config.desired_state == 'enable']
        wanted_disabled_user_services = [
            config.service for config in wanted_user_services if config.desired_state == 'disable']

        user_services_to_enable = [
            service for service in wanted_enabled_user_services if not self._systemd.service_enabled(service, user=True)]
        user_services_to_disable = [
            service for service in wanted_disabled_user_services if self._systemd.service_enabled(service, user=True)]

        return ServiceSyncStatus(system_services_to_disable, system_services_to_enable, user_services_to_disable, user_services_to_enable)

    def print_ufw_status(self) -> None:
        sync = UfwSync(self._ufw, self._console, self._system_config)
        sync.print_summary()

    def run(self, scope: SyncScope) -> None:
        """Runs a sync which will remove additional and install missing packages"""

        if scope.packages:
            self._run_packages()

        if scope.services:
            self._run_services()

        if scope.ufw:
            self._run_ufw()

    def _run_ufw(self) -> None:
        sync = UfwSync(self._ufw, self._console, self._system_config)
        sync.run()

    def _run_packages(self) -> None:
        status = self.package_status()

        sync = PackageSync(status, self._console, self._system_config.hooks_directory())
        sync.print_summary()

        answer = Prompt.ask('Do you want to continue?', choices=[
                            'yes', 'no'], default='yes', case_sensitive=False)
        if answer != 'yes':
            return

        sync.run(self._pacman, self._yay)

    def _run_services(self) -> None:
        status = self.service_status()
        sync = ServicesSync(status, self._console)
        sync.print_summary()

        answer = Prompt.ask('Do you want to continue?', choices=[
                            'yes', 'no'], default='yes', case_sensitive=False)
        if answer != 'yes':
            return

        sync.run(self._systemd)
