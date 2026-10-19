from .commands import api, auth, recipes  # noqa: F401
from .commands.cli import CLI


def main() -> None:
    CLI.click()


if __name__ == '__main__':
    main()
