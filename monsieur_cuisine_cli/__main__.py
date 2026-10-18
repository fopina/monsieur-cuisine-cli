from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .auth import _session_path, get_profile, login


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='monsieur-cuisine', description='Manage recipes in a monsieur-cuisine.com account.')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    commands = parser.add_subparsers(dest='command', required=True)

    auth = commands.add_parser('auth', help='Manage your account session.')
    auth_commands = auth.add_subparsers(dest='auth_command', required=True)
    login_parser = auth_commands.add_parser('login', help='Sign in through the Monsieur Cuisine mobile app OAuth flow.')
    login_parser.add_argument('--language', default='pt-PT', help='sign-in locale (default: pt-PT)')
    login_parser.add_argument('--browser', help='Playwright browser engine: chromium, firefox, or webkit (default: chromium)')
    login_parser.add_argument('--redirect-uri', default='lidl-com.monsieur-cuisine.companion://login/prod', help='OAuth callback URI (default: mobile app URI)')
    auth_commands.add_parser('status', help='Check whether an account session is saved locally.')
    auth_commands.add_parser('logout', help='Remove the saved account session.')
    commands.add_parser('profile', help='Fetch the authenticated account profile.')
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == 'auth' and args.auth_command == 'login':
            login(args.language, args.browser, args.redirect_uri)
        elif args.command == 'auth' and args.auth_command == 'status':
            print('A session is saved.' if _session_path().is_file() else 'No session is saved.')
        elif args.command == 'auth' and args.auth_command == 'logout':
            path = _session_path()
            if path.exists():
                path.unlink()
                print('Saved session removed.')
            else:
                print('No saved session to remove.')
        elif args.command == 'profile':
            print(json.dumps(get_profile(), indent=2, ensure_ascii=False))
    except (RuntimeError, KeyboardInterrupt) as exc:
        if isinstance(exc, KeyboardInterrupt):
            print('\nLogin cancelled.', file=sys.stderr)
            return 130
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
