
from typing import Literal
import re


class DefaultUfwRule:
    rule: Literal['deny', 'allow']
    type: Literal['in', 'out']

    def __init__(self,
                 type: Literal['in', 'out'],
                 rule: Literal['allow', 'deny']):
        self.type = type
        self.rule = rule

    @staticmethod
    def fromBitmanConfig(line: str):
        if ('in' in line):
            return DefaultUfwRule('in', 'deny' if 'deny' in line else 'allow')
        if ('out' in line):
            return DefaultUfwRule('out', 'deny' if 'deny' in line else 'allow')
        raise UfwConfigParseException(f"Invalid default ufw config: {line}")

    @staticmethod
    def fromUfwStatus(line: str):
        is_deny_in = 'deny (incoming)' in line
        is_allow_out = 'allow (outgoing)' in line
        return [
            DefaultUfwRule('in', 'deny' if is_deny_in else 'allow'),
            DefaultUfwRule('out', 'allow' if is_allow_out else 'deny')
        ]


class UfwRule:
    index: int | None
    type: Literal['in']
    rule: Literal['allow', 'deny']
    proto: Literal['any', 'tcp', 'udp']
    port: int | str
    fromIp: str

    def __init__(self,
                 index: int | None,
                 type: Literal['in', 'out'],
                 rule: Literal['allow', 'deny'],
                 proto: Literal['any', 'tcp', 'udp'],
                 port: int | str,
                 fromIp: str):
        self.index = index
        self.type = type
        self.rule = rule
        self.proto = proto
        self.fromIp = fromIp
        self.port = port

    @staticmethod
    def fromBitmanConfig(line: str):
        type, rule, port, proto, fromIp = line.split('\t', 5)
        if type != 'in':
            raise UfwConfigParseException(f"Invalid UFW Config type: {type}")
        if rule != 'allow' or rule != 'deny':
            raise UfwConfigParseException(f"Invalid UFW Config rule: {rule}")
        if proto != 'any' or proto != 'tcp' or proto != 'udp':
            raise UfwConfigParseException(f"Invalid UFW Config proto: {proto}")
        if port == '':
            raise UfwConfigParseException(f"Invalid UFW Config port: {port}")
        if fromIp == '':
            raise UfwConfigParseException(f"Invalid UFW Config fromIp: {fromIp}")

        return UfwRule(None, type, rule, proto, port, fromIp)

    @staticmethod
    def fromUfwStatus(line: str):
        pattern = r"(\[\s*(?P<index>\d+)\])\s*(?P<port_proto>[\w\/]+)( \(v6\))?\s+(?P<rule>ALLOW|DENY) (?P<type>IN|OUT)\s+(?P<fromIp>.+)"
        match = re.match(pattern, line.strip())
        if not match:
            raise UfwStatusParseException(f"Invalid UFW status line: {line}")

        port_proto = match.group("port_proto")
        rule = match.group("rule").lower()
        type = match.group("type").lower()
        fromIp = match.group("fromIp").strip()
        index = match.group("index")

        if '/' in port_proto:
            port, proto = port_proto.split('/', 2)
        else:
            port, proto = port_proto, 'any'

        if 'Anywhere' in fromIp:
            fromIp = 'any'

        if proto != 'any' or proto != 'tpc' or proto != 'udp':
            raise UfwStatusParseException(f"Invalid UFW status proto: {proto}")
        if fromIp == '':
            raise UfwStatusParseException(f"Invalid UFW status fromIp: {fromIp}")
        return UfwRule(int(index), type, rule, proto, port, fromIp)


class UfwConfigParseException(BaseException):
    pass


class UfwStatusParseException(BaseException):
    pass
