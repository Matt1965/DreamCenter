from dreamcenter.game import start_game
import click


#@click.group()
def main():
    """
    Entrypoint for game
    """
    start_game()


#@main.command(help="launches game")
#def launch():
#    start_game()
#
#
if __name__ == "__main__":
    import cProfile
    cProfile.run('main()', "output.dat")

    import pstats
    from pstats import SortKey

    with open("output_time.txt", "w") as f:
        p = pstats.Stats("output.dat", stream=f)
        p.sort_stats("time").print_stats()

    with open("output_calls.txt", "w") as f:
        p = pstats.Stats("output.dat", stream=f)
        p.sort_stats("calls").print_stats()