from dreamcenter.game import DreamGame

def launch():
    game = DreamGame.create()
    game.loop()


if __name__ == "__main__":
    launch()
