import argparse
import bitman

app = bitman.Bitman()

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
sync_parser.add_argument('--status', action='store_true',
                         help='List which packages are missing and which are additionally installed compared to bitman configuration')
sync_parser.set_defaults(func=app.sync)

args = parser.parse_args()
args.func(args)
