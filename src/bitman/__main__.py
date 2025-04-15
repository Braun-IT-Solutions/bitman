import argparse
import bitman

parser = argparse.ArgumentParser(
    prog='bitman',
    description='A declarative package manager for Arch Linux'
)
subparsers = parser.add_subparsers()

user_parser = subparsers.add_parser('user', help='User Commands')

user_subparsers = user_parser.add_subparsers()

user_setup_parser = user_subparsers.add_parser('setup', help='Setup bitman for this user')

user_install_parser = user_subparsers.add_parser('install', help='Install packages for user branch')
user_install_parser.add_argument('--aur', help='Install packages from the AUR', action='store_true')
user_install_parser.add_argument('packages', nargs='+', help='The packages you want to install')

sync_parser = subparsers.add_parser('sync', help='Sync Commands')

print(parser.parse_args())

app = bitman.Bitman()
