
import subprocess


class GitRepository:
    def __init__(self, directory: str):
        self._directory = directory

    def branches(self) -> list[str]:
        """Returns a list of all available branch names"""
        result = subprocess.run(
            ['git', 'branch', '--all', '--format="%(refname:short)"'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False,
            cwd=self._directory
        )
        result.check_returncode()
        return [line.removeprefix('"').removesuffix('"') for line in result.stdout.splitlines()]

    def active_branch(self) -> str:
        """Returns the currently active branch"""
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False,
            cwd=self._directory
        )
        result.check_returncode()
        return result.stdout

    def change_branch(self, branch: str) -> None:
        """Changes to the specified branch"""
        result = subprocess.run(
            ['git', 'switch', branch],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False,
            cwd=self._directory
        )
        result.check_returncode()

    def pull(self) -> None:
        """Pulls changes for the active branch"""
        result = subprocess.run(
            ['git', 'pull'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            check=False,
            cwd=self._directory
        )
        result.check_returncode()


class Git:
    def clone(self, repository: str, directory: str) -> GitRepository:
        """Clones a git repository into the specified directory"""
        temp_path = '/tmp/bitman/config'

        # We copy to a temporary path first, as git won't ask for SSH when using sudo
        result = subprocess.run(
            ['git', 'clone', repository, temp_path],
            encoding='utf-8',
            check=False
        )
        result.check_returncode()

        result = subprocess.run(
            ['sudo', 'mv', temp_path, directory],
            encoding='utf-8',
            check=False
        )
        result.check_returncode()

        return GitRepository(directory)
