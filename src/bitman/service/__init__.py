import subprocess


class Systemd:
    def service_enabled(self, service: str, user: bool = False) -> bool:
        result = subprocess.run(
            filter(None, ['systemctl', '--user' if user else '', 'is-enabled', service]),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        if result.returncode != 0 and result.stderr:
            result.check_returncode()
        return result.stdout.startswith('enabled')

    def service_running(self, service: str, user: bool = False) -> bool:
        result = subprocess.run(
            filter(None, ['systemctl', '--user' if user else '', 'is-active', '--quiet', service]),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        return result.returncode == 0

    def enable_service(self, service: str, now: bool = False, user: bool = False) -> None:
        result = subprocess.run(
            filter(None, ['sudo' if not user else '', 'systemctl', '--user' if user else '',
                   'enable', '--now' if now else '', service]),
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

    def disable_service(self, service: str, now: bool = False, user: bool = False) -> None:
        result = subprocess.run(
            filter(None, ['sudo' if not user else '', 'systemctl', '--user' if user else '',
                   'disable', '--now' if now else '', service]),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()

    def reload_daemon(self, user: bool = False) -> None:
        result = subprocess.run(
            filter(None, ['sudo' if not user else '', 'systemctl', '--user' if user else '',
                   'daemon-reload']),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False
        )
        result.check_returncode()
