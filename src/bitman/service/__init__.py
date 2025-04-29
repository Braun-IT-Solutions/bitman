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
