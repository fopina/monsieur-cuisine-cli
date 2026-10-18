import json

import click
import classyclick

from . import __version__
from .auth import _session_path, get_profile, login


class CLI(classyclick.Group):
    """Manage recipes in a monsieur-cuisine.com account."""

    __config__ = classyclick.Group.Config(
        name='monsieur-cuisine',
        decorators=click.version_option(version=__version__),
    )


class Auth(CLI.SubGroup):
    """Manage the account session."""


class Login(Auth.Command):
    """Sign in through Lidl's account login."""

    language: str = classyclick.Option(default='pt-PT', help='Sign-in locale (default: pt-PT).')
    browser: bool = classyclick.Option(default=False, help='Use the system browser and paste the final mobile callback URL.')
    redirect_uri: str = classyclick.Option(
        default='lidl-com.monsieur-cuisine.companion://login/prod',
        help='OAuth callback URI (default: mobile app URI).',
    )

    def __call__(self):
        try:
            login(language=self.language, system_browser=self.browser, redirect_uri=self.redirect_uri)
        except KeyboardInterrupt as exc:
            raise click.Abort() from exc
        except RuntimeError as exc:
            raise click.ClickException(str(exc)) from exc


class Status(Auth.Command):
    """Check whether an account session is saved locally."""

    def __call__(self):
        click.echo('A session is saved.' if _session_path().is_file() else 'No session is saved.')


class Logout(Auth.Command):
    """Remove the saved account session."""

    def __call__(self):
        path = _session_path()
        if path.exists():
            path.unlink()
            click.echo('Saved session removed.')
        else:
            click.echo('No saved session to remove.')


class Profile(CLI.Command):
    """Fetch the authenticated account profile."""

    def __call__(self):
        try:
            click.echo(json.dumps(get_profile(), indent=2, ensure_ascii=False))
        except RuntimeError as exc:
            raise click.ClickException(str(exc)) from exc


def main() -> None:
    CLI.click()


if __name__ == '__main__':
    main()
