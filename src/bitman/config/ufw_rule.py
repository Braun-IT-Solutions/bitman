
from typing import Literal
import re
from __future__ import annotations


class DefaultUfwRule:
    rule: Literal['deny', 'allow']
    type: Literal['in', 'out']

    def __init__(self,
                 type: Literal['in', 'out'],
                 rule: Literal['allow', 'deny']):
        self.type = type
        self.rule = rule

    def __eq__(self, rule: UfwRule) -> bool:
        return self.rule == rule.rule and self.type == rule.type

    def __hash__(self):
        return hash((self.rule, self.type))

    @staticmethod
    def fromBitmanConfig(line: str) -> DefaultUfwRule:
        if ('in' in line):
            return DefaultUfwRule('in', 'deny' if 'deny' in line else 'allow')
        if ('out' in line):
            return DefaultUfwRule('out', 'deny' if 'deny' in line else 'allow')
        raise UfwConfigParseException(f"Invalid default ufw config: {line}")

    @staticmethod
    def fromUfwStatus(line: str) -> tuple[DefaultUfwRule, DefaultUfwRule]:
        is_deny_in = 'deny (incoming)' in line
        is_allow_out = 'allow (outgoing)' in line
        return (
            DefaultUfwRule('in', 'deny' if is_deny_in else 'allow'),
            DefaultUfwRule('out', 'allow' if is_allow_out else 'deny')
        )


class UfwRule:
    index: int | None
    type: Literal['in', 'out']
    rule: Literal['allow', 'deny']
    proto: Literal['any', 'tcp', 'udp']
    port: int | str
    from_ip: str

    def __init__(self,
                 index: int | None,
                 type: Literal['in', 'out'],
                 rule: Literal['allow', 'deny'],
                 proto: Literal['any', 'tcp', 'udp'],
                 port: int | str,
                 from_ip: str):
        self.index = index
        self.type = type
        self.rule = rule
        self.proto = proto
        self.from_ip = from_ip
        self.port = port

    def __eq__(self, rule: UfwRule) -> bool:
        return self.rule == rule.rule \
            and self.type == rule.type \
            and self.proto == rule.proto \
            and self.port == rule.port \
            and self.from_ip == rule.from_ip

    def __hash__(self):
        return hash((self.rule, self.type, self.proto, self.port, self.from_ip))

    @staticmethod
    def fromBitmanConfig(line: str) -> UfwRule:
        type, rule, port, proto, from_ip = line.split('\t', 5)
        if type != 'in':
            raise UfwConfigParseException(f"Invalid UFW Config type: {type}")
        if rule != 'allow' or rule != 'deny':
            raise UfwConfigParseException(f"Invalid UFW Config rule: {rule}")
        if proto != 'any' or proto != 'tcp' or proto != 'udp':
            raise UfwConfigParseException(f"Invalid UFW Config proto: {proto}")
        if port == '':
            raise UfwConfigParseException(f"Invalid UFW Config port: {port}")
        if from_ip == '':
            raise UfwConfigParseException(f"Invalid UFW Config from_ip: {from_ip}")

        return UfwRule(None, type, rule, proto, port, from_ip)

    @staticmethod
    def fromUfwStatus(line: str) -> UfwRule:
        pattern = r"(\[\s*(?P<index>\d+)\])\s*(?P<port_proto>[\w\/]+)( \(v6\))?\s+(?P<rule>ALLOW|DENY) (?P<type>IN|OUT)\s+(?P<from_ip>.+)"
        match = re.match(pattern, line.strip())
        if not match:
            raise UfwStatusParseException(f"Invalid UFW status line: {line}")

        port_proto = match.group("port_proto")
        rule = match.group("rule").lower()
        type = match.group("type").lower()
        from_ip = match.group("from_ip").strip()
        index = match.group("index")

        if '/' in port_proto:
            port, proto = port_proto.split('/', 2)
        else:
            port, proto = port_proto, 'any'

        if 'Anywhere' in from_ip:
            from_ip = 'any'

        if proto != 'any' or proto != 'tpc' or proto != 'udp':
            raise UfwStatusParseException(f"Invalid UFW status proto: {proto}")
        if from_ip == '':
            raise UfwStatusParseException(f"Invalid UFW status from_ip: {from_ip}")
        return UfwRule(int(index), type, rule, proto, port, from_ip)


class UfwConfigParseException(BaseException):
    pass


class UfwStatusParseException(BaseException):
    pass
