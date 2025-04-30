import subprocess
from config.ufw_rule import UfwRule, DefaultUfwRule
from typing import Generator, Tuple


class Ufw:
    def __init__(self):
        self._rules = None
        self._default_rules = None
        self._current_verbose = self._verbose_status()
        self._current_numbered_status = self._numbered_status()

    def update_status(self):
        self._current_verbose = self._verbose_status()
        self._current_numbered_status = self._numbered_status()

    def is_enabled(self) -> bool:
        return 'Status: active' in self._current_verbose

    def reload(self) -> None:
        self._rules = None
        self._default_rules = None
        result = subprocess.run(
            ['ufw', 'reload'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()

    def enable(self) -> None:
        result = subprocess.run(
            ['ufw', 'enable'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()

    def disable(self) -> None:
        result = subprocess.run(
            ['ufw', 'disable'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()

    def reset(self) -> None:
        result = subprocess.run(
            ['ufw', 'reset'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()

    def rules(self) -> Generator[UfwRule, None, None]:
        if self._rules != None:
            yield from self._rules
            return
        rules = []
        for line in self._current_numbered_status:
            line = line.strip()
            if line.startswith('['):
                rule = UfwRule.fromUfwStatus(line)
                rules.append(rule)
                yield rule
        self._rules = rule

    def default_rules(self) -> Tuple[DefaultUfwRule, DefaultUfwRule]:
        if self._default_rules != None:
            return self._default_rules
        for line in self._current_verbose:
            line = line.strip()
            if line.startswith('Default: '):
                self._default_rules = DefaultUfwRule.fromUfwStatus(line)
                return self._default_rules
        raise UfwStatusParseException(f"Where default ufw status?")

    def delete_rules(self, rules: list[UfwRule]) -> None:
        rules = rules.sort(key=lambda rule: rule.index, reverse=True)
        for rule in rules:
            if rule == None:
                raise UfwDeleteRuleException(f"Invalid rule index")
            result = subprocess.run(
                ['ufw', 'delete', rule.index],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                check=False
            )
            result.check_returncode()

    def missing_rules(self, rules_should_exist: list[UfwRule]) -> set[UfwRule]:
        rules = set(self.rules())
        should_exist = set(rules_should_exist)
        return should_exist.difference(rules)

    def rules_to_delete(self, rules_should_exist: list[UfwRule]) -> set[UfwRule]:
        rules = set(self.rules())
        should_exist = set(rules_should_exist)
        return rules.difference(should_exist)

    def default_not_equal(self, expected_default_rules: tuple[DefaultUfwRule, DefaultUfwRule]) -> list[DefaultUfwRule]:
        default_rules = self.default_rules()
        result = []
        if expected_default_rules[0] != default_rules[0]:
            result.append(expected_default_rules[0])
        if expected_default_rules[1] != default_rules[1]:
            result.append(expected_default_rules[1])
        return result

    def add_rule(self, rule: UfwRule) -> None:
        result = subprocess.run(
            ['ufw', rule.rule, rule.type, 'on', rule.from_ip, 'to', rule.proto, rule.port],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()

    def set_default_rule(self, rule: DefaultUfwRule) -> None:
        result = subprocess.run(
            ['ufw', 'default', rule.rule, 'incoming' if rule.type == 'in' else 'outgoing'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()

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


class UfwDeleteRuleException(BaseException):
    pass
