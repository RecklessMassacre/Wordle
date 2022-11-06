import sqlite3
from os.path import exists


class DBHandler:
    """Create object with connection to db (sqlite3)"""

    # committing after every query so i can see how db changes in console
    # errors cannot occur ... so fuck try except
    def __init__(self, db_file: str):
        """:param db_file: path to db file"""
        if not exists(db_file):
            raise sqlite3.Error("U lost y db lol")

        self.__conn: sqlite3.Connection = sqlite3.connect(db_file)
        self.__cur: sqlite3.Cursor = self.__conn.cursor()
        self.__on_connect()

        if not self.__check_db_init():
            self.__setup_empty_db()

        # creates a list of callable funcs to change certain value
        # in distribution table
        # d is dict for interpreting numbers to column names
        self.__d: dict = {
            1: 'first', 2: 'second', 3: 'third',
            4: 'fourth', 5: 'fifth', 6: 'sixth',
        }
        self.__func_arr: list = [
            lambda i=i: self.__cur.execute(
                f"UPDATE distribution SET {self.__d[i]}_try = {self.__d[i]}_try + 1 "
                f"WHERE user_id = (SELECT id FROM user WHERE is_current = 1)"
            ) for i in range(1, 7)
        ]

    # asd
    def __check_db_init(self) -> bool:
        """Checks if db is initialized"""
        self.__cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        arr = self.__cur.fetchall()

        return True if arr else False

    def __setup_empty_db(self):
        """Setups empty tables in db (except table with words)"""
        self.__cur.execute(
            "CREATE TABLE IF NOT EXISTS user (id INTEGER, nick_name TEXT NOT NULL, "
            "is_current INTEGER, PRIMARY KEY (id))"
        )
        self.__cur.execute(
            "CREATE TABLE IF NOT EXISTS stats (user_id INTEGER, played INTEGER, games_won INTEGER,"
            "games_lost INTEGER, current_streak INTEGER, max_streak INTEGER, FOREIGN KEY (user_id) "
            "REFERENCES user(id) ON DELETE CASCADE ON UPDATE NO ACTION)"
        )
        self.__cur.execute(
            "CREATE TABLE IF NOT EXISTS distribution (user_id INTEGER, first_try INTEGER, second_try INTEGER,"
            "third_try INTEGER, fourth_try INTEGER, fifth_try INTEGER, sixth_try INTEGER, FOREIGN KEY (user_id) "
            "REFERENCES user(id) ON DELETE CASCADE ON UPDATE NO ACTION)"
        )
        self.__cur.execute(
            "CREATE TABLE IF NOT EXISTS game_state (user_id INTEGER,k_state_string TEXT, "
            "l_state_string TEXT, word TEXT, FOREIGN KEY (user_id) REFERENCES user(id) "
            "ON DELETE CASCADE ON UPDATE NO ACTION)"
        )

        self.__cur.execute("CREATE TABLE IF NOT EXISTS autosave (activated INTEGER)")
        self.__cur.execute("INSERT INTO autosave (activated) VALUES (0)")
        self.__cur.execute(
            "CREATE VIEW get_user AS SELECT u.nick_name, u.is_current, s.played, s.games_won, s.games_lost, "
            "s.current_streak, s.max_streak,d.first_try, d.second_try, d.third_try, d.fourth_try, d.fifth_try, "
            "d.sixth_try FROM user u LEFT JOIN stats s on u.id = s.user_id LEFT JOIN distribution d on u.id = d.user_id"
        )
        self.__conn.commit()

    def __on_connect(self):
        """Toggle on foreign keys in db"""
        self.__cur.execute("PRAGMA foreign_keys = ON")
        self.__conn.commit()

    def unset_current_user(self, nick_name):
        """Unset current user in db"""
        self.__cur.execute("UPDATE user set is_current = 0 WHERE nick_name =?", (nick_name,))
        self.__conn.commit()

    def get_current_user_nick(self) -> str:
        """Get current user nick"""
        self.__cur.execute("SELECT nick_name FROM user WHERE is_current = 1")
        tarr = self.__cur.fetchall()
        if tarr:
            return tarr[0][0]
        else:
            return ''

    def get_current_user(self) -> tuple:
        """Get all stuff for statistics window"""
        self.__cur.execute("SELECT * FROM get_user WHERE is_current = 1")
        tarr = self.__cur.fetchall()
        if tarr:
            return tarr[0]
        else:
            return ()

    def set_current_user(self, username: str):
        """Set user with provided username to be current in db"""
        self.__cur.execute("UPDATE user SET is_current = 1 WHERE nick_name = ?", (username,))
        self.__conn.commit()

    def user_exists(self, username: str) -> bool:
        """Check if user with provided username exists in db"""
        self.__cur.execute("SELECT nick_name FROM user WHERE nick_name = ?", (username,))
        arr = self.__cur.fetchall()
        return True if arr else False

    def delete_user(self, username):
        """Delete user with provided username from db"""
        self.__cur.execute("DELETE FROM user WHERE nick_name = ?", (username,))
        self.__conn.commit()

    def add_user(self, username) -> bool:
        """Add user with provided username to db

        returns:
            False if user username already exists, True if user is added
        """
        if self.user_exists(username):
            return False

        self.__cur.execute("INSERT INTO user (nick_name, is_current) VALUES (?, 0)", (username,))
        self.__cur.execute(
            "INSERT INTO stats(user_id, played, games_won, games_lost, current_streak, max_streak)"
            "VALUES (last_insert_rowid(), 0, 0, 0, 0, 0)"
        )
        self.__cur.execute(
            "INSERT INTO distribution(user_id, first_try, second_try, third_try, fourth_try, fifth_try, sixth_try)"
            "VALUES (last_insert_rowid(), 0, 0, 0, 0, 0, 0)"
        )
        self.__cur.execute(
            'INSERT INTO game_state (user_id, k_state_string, l_state_string, word) '
            'VALUES (last_insert_rowid(), "", "", "")'
        )
        self.__conn.commit()
        return True

    def get_users(self) -> list[tuple]:
        """Get all users from db

        return:
            list with tuples, each represents distinct user"""
        self.__cur.execute("SELECT * FROM user")

        arr = self.__cur.fetchall()
        return arr

    def get_words(self) -> list[str]:
        """Get all words from db

        return:
            list with words"""
        self.__cur.execute("SELECT * FROM words")

        arr = [item[0] for item in self.__cur.fetchall()]
        return arr

    def get_autosave_opt(self) -> int:
        """Get autosave option from db

        returns:
            1 = on, 0 = off"""
        self.__cur.execute("SELECT * FROM autosave")
        arr = self.__cur.fetchall()

        return arr[0][0]

    def switch_autosave(self):
        """Switch autosave option in db"""
        self.__cur.execute("UPDATE autosave SET activated = not activated")
        self.__conn.commit()

    def add_loss(self):
        """Add loss to current user in db"""
        self.__cur.execute(
            "UPDATE stats SET played = played + 1, games_lost = games_lost + 1, current_streak = 0 "
            "WHERE user_id = (SELECT id FROM user WHERE is_current = 1)"
        )
        self.__conn.commit()

    def add_win(self, cur_row: int):
        """Add win to current user in db

        param:
            cur_row - current row when game was finished"""
        self.__cur.execute(
            "UPDATE stats SET played = played + 1, games_won = games_won + 1, current_streak = current_streak + 1, "
            "max_streak = MAX(current_streak + 1, max_streak) WHERE user_id = "
            "(SELECT id FROM user WHERE is_current = 1) "
        )

        self.__func_arr[cur_row - 1]()
        self.__conn.commit()

    def save_state(self, btn: str, lbl: str, word: str):
        """Save str representations of keyboard, labels and chosen word to db

        params
            btn - str representations of keyboard state

            lbl - str representations of labels state
            word - chosen word"""
        self.__cur.execute(
            "UPDATE game_state SET k_state_string = ?, l_state_string = ?, word = ? " 
            "WHERE user_id = (SELECT id FROM user WHERE is_current = 1)", (btn, lbl, word)
        )
        self.__conn.commit()

    def get_state(self) -> tuple[str]:
        """Get saved str representations of keyboard, labels and chosen word from db

        return:
            tuple with 3 elements:
                1 - str representations of keyboard state

                2 - str representations of labels states

                3 - chosen word"""
        self.__cur.execute(
            "SELECT k_state_string, l_state_string, word FROM game_state "
            "WHERE user_id = (SELECT id FROM user WHERE is_current = 1)"
        )
        arr = self.__cur.fetchall()
        return arr[0]

    def check_state(self) -> bool:
        """Check if there is a saved game in db

        returns:
            True - yes

            False - no"""
        self.__cur.execute(
            "SELECT word FROM game_state "
            "WHERE user_id = (SELECT id FROM user WHERE is_current = 1)"
        )

        tpl = self.__cur.fetchone()
        if tpl:
            return True if tpl[0] else False

        return False

    def close(self):
        """Close connection to db"""
        self.__conn.close()
