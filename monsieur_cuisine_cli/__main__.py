from .cli import CLI
from .commands import api, auth, recipes  # noqa: F401


def main() -> None:
    CLI.click()


if __name__ == '__main__':
    main()
