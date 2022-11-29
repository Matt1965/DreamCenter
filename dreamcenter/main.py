from dreamcenter.game import start_game
import click

@click.group()
def main():
    """
    Entrypoint for game
    """

@main.command(help="launches game")
def launch():
    start_game()

if __name__ == "__main__":
    main()
