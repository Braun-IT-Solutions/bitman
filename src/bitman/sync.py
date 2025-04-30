from argparse import Namespace
from typing import NamedTuple
from rich.prompt import Prompt
from rich.console import Console
from bitman.config.system_config import SystemConfig
from bitman.package.pacman import Pacman
from bitman.package.yay import Yay
from bitman.package_sync import PackageSync, PackageSyncStatus
from bitman.service import Systemd
from bitman.ufw import Ufw


class ServiceSyncStatus(NamedTuple):
    system_to_disable: list[str]
    system_to_enable: list[str]
    user_to_disable: list[str]
    user_to_enable: list[str]


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

    def print_ufw_status(self) -> bool:
        if not self._ufw.is_enabled():
            self._console.print("Ufw is disabled should be enabled")
            return True

        expected_default_rules = list(self._system_config.default_ufw_rules())
        expected_rules = list(self._system_config.ufw_rules())

        unsynced_default_rules = self._ufw.default_not_equal(expected_default_rules)
        missing_rules = self._ufw.missing_rules(expected_rules)
        rules_to_delete = self._ufw.rules_to_delete(expected_rules)

        if len(unsynced_default_rules) == 0 and len(missing_rules) == 0 and len(rules_to_delete) == 0:
            self._console.print('All ufw rules in sync', style='green')
            return False
        if len(unsynced_default_rules) != 0:
            self._console.print('Unsynced default rules', style='bold yellow')
            self._console.print(
                *[f'[bold]·[/bold] {rule}' for rule in unsynced_default_rules], sep='\n')
        if len(missing_rules) != 0:
            self._console.print('Missing rules', style='bold yellow')
            self._console.print(
                *[f'[bold]·[/bold] {rule}' for rule in missing_rules], sep='\n')
        if len(rules_to_delete) != 0:
            self._console.print('Rules to delete', style='bold yellow')
            self._console.print(
                *[f'[bold]·[/bold] {rule}' for rule in rules_to_delete], sep='\n')
        return True

    def run(self, scope: SyncScope) -> None:
        """Runs a sync which will remove additional and install missing packages"""

        if scope.packages:
            self._run_packages()

        if scope.services:
            self._run_services()

        if scope.ufw:
            self._run_ufw()

    def _run_ufw(self) -> None:
        if not self._ufw.is_enabled():
            answer = Prompt.ask('UFW needs to be enabled to start configuring, do you want to continue?', choices=[
                'yes', 'no'], default='yes', case_sensitive=False)
            if answer != 'yes':
                return

            self._console.print('Enable ufw', style='bold yellow')
            self._ufw.enable()
            self._ufw.update_status()

        is_not_synced = self.print_ufw_status()

        if not is_not_synced:
            return

        answer = Prompt.ask('Do you want to continue?', choices=[
                            'yes', 'no'], default='yes', case_sensitive=False)
        if answer != 'yes':
            return

        expected_default_rules = list(self._system_config.default_ufw_rules())
        expected_rules = list(self._system_config.ufw_rules())

        unsynced_default_rules = self._ufw.default_not_equal(expected_default_rules)
        missing_rules = self._ufw.missing_rules(expected_rules)
        rules_to_delete = self._ufw.rules_to_delete(expected_rules)

        if len(unsynced_default_rules) == 0 and len(missing_rules) == 0 and len(rules_to_delete) == 0:
            self._console.print('All ufw rules in sync', style='green')
            return

        if len(unsynced_default_rules) != 0:
            self._console.print('Syncing default rules', style='bold yellow')
            for rule in unsynced_default_rules:
                self._console.print(f"Set default to: {rule}", style='yellow')
                self._ufw.set_default_rule(rule)

        if len(rules_to_delete) != 0:
            self._console.print('Deleting rules', style='bold yellow')
            self._ufw.delete_rules(list(rules_to_delete))
        if len(missing_rules) != 0:
            self._console.print('Add missing rules', style='bold yellow')
            for rule in missing_rules:
                self._console.print(f"Add rule: {rule}", style='yellow')
                self._ufw.add_rule(rule)

        self._console.print('Reload ufw', style='bold yellow')
        self._ufw.reload()

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
        if len(status.system_to_disable) == 0 and len(status.system_to_enable) == 0 and len(status.user_to_disable) == 0 and len(status.user_to_enable) == 0:
            self._console.print('Everything in sync, nothing to do', style='bold green')
            return

        if len(status.system_to_enable) > 0:
            self._console.print(
                'The following system services will be [bold]enabled[/bold]:', style='yellow')
            self._console.print(
                *['[bold]·[/bold] ' + service for service in status.system_to_enable], sep='\n', highlight=False)
            self._console.line()

        if len(status.system_to_disable) > 0:
            self._console.print(
                'The following system services will be [bold]disabled[/bold]:', style='yellow')
            self._console.print(
                *['[bold]·[/bold] ' + service for service in status.system_to_disable], sep='\n', highlight=False)
            self._console.line()

        if len(status.user_to_enable) > 0:
            self._console.print(
                'The following user services will be [bold]enabled[/bold]:', style='yellow')
            self._console.print(
                *['[bold]·[/bold] ' + service for service in status.user_to_enable], sep='\n', highlight=False)
            self._console.line()

        if len(status.user_to_disable) > 0:
            self._console.print(
                'The following user services will be [bold]disabled[/bold]:', style='yellow')
            self._console.print(
                *['[bold]·[/bold] ' + service for service in status.user_to_disable], sep='\n', highlight=False)
            self._console.line()

        answer = Prompt.ask('Do you want to continue?', choices=[
                            'yes', 'no'], default='yes', case_sensitive=False)
        if answer != 'yes':
            return

        for service in status.system_to_enable:
            self._console.print(f'Enabling {service}...', end='')
            self._systemd.enable_service(service)
            self._console.print(' Done!')

        for service in status.user_to_enable:
            self._console.print(f'Enabling {service}...', end='')
            self._systemd.enable_service(service, user=True)
            self._console.print(' Done!')

        for service in status.system_to_disable:
            self._console.print(f'Disbling {service}...', end='')
            self._systemd.disable_service(service)
            self._console.print(' Done!')

        for service in status.user_to_disable:
            self._console.print(f'Disbling {service}...', end='')
            self._systemd.disable_service(service, user=True)
            self._console.print(' Done!')
