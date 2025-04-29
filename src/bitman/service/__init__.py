import subprocess


class Systemd:
    def service_enabled(self, service: str) -> bool:
        result = subprocess.run(
            ['systemctl', 'is-enabled', service],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        if result.returncode != 0 and result.stderr:
            result.check_returncode()
        return result.stdout.startswith('enabled')

    def service_running(self, service: str) -> bool:
        result = subprocess.run(
            ['systemctl', 'is-active', '--quiet', service],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        return result.returncode == 0

    def enable_service(self, service: str, now: bool = False) -> None:
        result = subprocess.run(
            filter(None, ['sudo', 'systemctl', 'enable', '--now' if now else '', service]),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        try:
            result.check_returncode()
        except Exception as e:
            print('Error')
            print(e)
            print(result.stderr)

    def disable_service(self, service: str, now: bool = False) -> None:
        result = subprocess.run(
            filter(None, ['sudo', 'systemctl', 'disable', '--now' if now else '', service]),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()
