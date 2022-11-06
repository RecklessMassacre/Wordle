from main_window import _Wordle
from os.path import join, dirname, relpath


class WordleGame:
    """Wordle game

    Use .run() to run the game
    """
    def __init__(self):
        self.__db_path = relpath("../data/data.db", dirname(__file__))
        self.__wordle = _Wordle(self.__db_path)

    def run(self):
        self.__wordle.run()


if __name__ == "__main__":
    g = WordleGame()
    g.run()
