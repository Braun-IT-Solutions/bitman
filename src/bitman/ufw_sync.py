from rich.console import Console
from rich.prompt import Prompt

from bitman.config.system_config import SystemConfig
from bitman.ufw import Ufw


class UfwSync:
    def __init__(self, ufw: Ufw, console: Console, system_config: SystemConfig):
        self._ufw = ufw
        self._console = console
        self._system_config = system_config

    def print_summary(self) -> bool:
        if not self._ufw.is_enabled():
            answer = Prompt.ask('UFW needs to be enabled to query the current UFW state, do you want to enable it?', choices=[
                'yes', 'no'], default='yes', case_sensitive=False)
            if answer != 'yes':
                return False

            self._console.print('Enable ufw', style='bold yellow')
            self._ufw.enable()
            self._ufw.update_status()

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

    def run(self) -> None:
        is_not_synced = self.print_summary()

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
