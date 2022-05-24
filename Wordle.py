import sqlite3
from typing import Optional, Union
from tkinter import Tk, Label, Frame, Button, PhotoImage, \
    StringVar, Toplevel, Canvas, Scrollbar, Entry, Checkbutton
from tkinter.constants import VERTICAL
from tkinter.messagebox import askokcancel, showinfo, WARNING
from random import sample
from os.path import exists
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


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


class Wordle(Tk):
    """Wordle game itself. Contains all the logic"""
    # architecture is shit
    def __init__(self, db_name: str):
        super().__init__()
        # sqlite3
        self.db_handler: DBHandler = DBHandler(db_name)

        # colors
        self.BASE_COLOR: str = '#f0f0f0'
        self.DT_BASE_COLOR: str = '#121212'

        self.BASE_LBL_COLOR: str = 'white'
        self.DT_LBL_COLOR: str = '#343434'

        self.BASE_BTN_COLOR: str = '#f0f0f0'
        self.DT_BTN_COLOR: str = 'grey'

        self.BASE_LETTERS_COLOR: str = 'black'
        self.DT_LETTERS_COLOR: str = '#F6F6F6'

        self.PAINTED_LETTERS_COLOR: str = '#EBEBEB'

        self.YELLOW: str = '#D8AF2E'
        self.GREEN: str = '#5EA83D'

        self.GREY: str = 'grey'
        self.DT_GREY: str = '#343434'

        # var for theme change
        self.__dark_theme_fl: bool = False

        # game data
        self.__autosave: bool = self.__load_autosave_opt()
        self.ROW_AMOUNT: int = 6
        self.ROW_LENGTH: int = 5
        self.__words_list: Optional[list[str]] = self.db_handler.get_words()  # all 5-letters words
        self.__chosen_word: str = sample(self.__words_list, 1)[0].upper()  # word to guess
        self.__input_word: list[str] = [str() for _ in range(self.ROW_LENGTH)]
        self.__cur_row: int = 1
        self.__label_pointer: int = 0
        self.__game_flag: bool = True
        # each number is alphabet position and each array position is keyboard position
        self.__numerical_keyboard: list[int] = [
            10, 23, 20, 11, 5, 14, 3, 25, 26, 8, 22, 27,
            21, 28, 2, 0, 16, 17, 15, 12, 4, 7, 30, 6,
            32, 24, 18, 13, 9, 19, 29, 1, 31
        ]

        # zero size image, used to make labels quadratic
        self.__image: PhotoImage = PhotoImage()

        # frames definition
        self.__gfield_frame: Frame = Frame(self)
        self.__menu_frame_left: Frame = Frame(self)
        self.__menu_frame_right: Frame = Frame(self)
        self.__keyboard_frame: Frame = Frame(self)
        self.__messages_frame: Frame = Frame(self)

        # labels and its requirements definition and initialization
        # message label
        self.__message_label: Optional[Label] = None
        self.__message_label_var: StringVar = StringVar()
        self.__message_label_var.set(
            'Привет! Для ввода букв с клавиатуры нужно перевести раскладку на англ.\n'
            'Для ведения статистики нужно создать профиль'
        )

        # game field labels
        self.__labels_dict: dict[str, Label] = {}
        self.__text_vars: list[StringVar] = [StringVar() for _ in range(self.ROW_LENGTH * self.ROW_AMOUNT)]
        self.__init_labels()

        # buttons and its requirements definition and initialization
        self.__alphabet: list[str] = [chr(i) for i in range(ord('а'), ord('а') + 6)] + \
                                     [chr(ord('а') + 33)] + \
                                     [chr(i) for i in range(ord('а') + 6, ord('а') + 32)]

        self.__state_to_color_dict: dict[int, str] = {
            0: self.BASE_BTN_COLOR, 1: self.GREY, 2: self.YELLOW, 3: self.GREEN
        }  # state: color
        self.__dt_state_to_color_dict: dict[int, str] = {
            0: self.DT_BTN_COLOR, 1: self.DT_GREY, 2: self.YELLOW, 3: self.GREEN
        }  # state: color
        self.__letter_to_button_name_dict: dict[str, str] = {
            y: f'btn{x}' for x, y in enumerate(self.__alphabet)
        }  # letter: button name
        self.__buttons_states: dict[str, int] = dict.fromkeys(self.__alphabet, 0)  # letter (not capital): state
        self.__btn_dict: dict[str, Button] = {}  # button name: button object
        self.__clear_button: Optional[Button] = None
        self.__enter_button: Optional[Button] = None
        self.__ng_button: Optional[Button] = None
        self.__stat_button: Optional[Button] = None
        self.__settings_button: Optional[Button] = None
        self.__profile_button: Optional[Button] = None

        self.__init_buttons()

        # root initialization
        self.__window_width: int = 820
        self.__window_length: int = 820
        self.__root_setup()

        # placing everything
        self.__place_frames()
        self.__place_labels()
        self.__place_buttons()

        self.__ask_load_game()

        self.protocol("WM_DELETE_WINDOW", self.__on_closing)

    def __ask_load_game(self):
        if self.__autosave:
            if self.db_handler.check_state():
                self.__create_ask_load_window()

    def __create_ask_load_window(self):
        width, length = 300, 100
        oc_window = OkCancelWindow(width, length, self)
        self.center_window(oc_window, width, length)

        # lock root window and put it behind new one
        oc_window.grab_set()
        self.lift()

    def init_game_data(self):
        """Load last saved game and substitute current data with loaded"""
        raw = self.db_handler.get_state()
        lbl, btn = {}, {}
        # [:-1] cuts last separator
        btn_raw, lbl_raw, word = raw[0][:-1].split('|'), raw[1][:-1].split('|'), raw[2]

        for item in btn_raw:
            temp = item.split(":")
            btn[temp[0]] = int(temp[1])

        for item in lbl_raw:
            temp = item.split(":")
            # i shouldn't load unpainted letters
            if temp[1] == 'white':
                temp[2] = ''
            lbl[temp[0]] = f"{temp[1]}:{temp[2]}"

        pointer = 0
        for value in lbl.values():
            if not value.split(":")[1]:
                break

            pointer += 1

        self.__cur_row = pointer // self.ROW_LENGTH + 1
        self.__label_pointer = pointer
        self.__buttons_states = btn
        self.__chosen_word = word

        # paint buttons
        for letter, state in self.__buttons_states.items():
            btn_name = self.__letter_to_button_name_dict[letter]
            color = self.__state_to_color_dict[state]
            self.__btn_dict[btn_name].config(bg=color)

        # put letters in labels and paint them
        for i in range(self.ROW_AMOUNT):
            for j in range(self.ROW_LENGTH):
                color, letter = lbl[f'lbl{i}{j}'].split(":")
                if letter:
                    ltr_color = self.PAINTED_LETTERS_COLOR
                else:
                    ltr_color = self.BASE_LETTERS_COLOR
                self.__labels_dict[f'lbl{i}{j}'].config(bg=color, fg=ltr_color)
                self.__text_vars[self.ROW_LENGTH * i + j].set(letter)

    def __load_autosave_opt(self):
        value = self.db_handler.get_autosave_opt()
        return True if value else False

    def change_autosave(self):
        """Switch autosave option both in db and wordle app"""
        self.__autosave = not self.__autosave
        self.db_handler.switch_autosave()

    def get_current_user(self) -> str:
        """Get current user's username from db

        return:
            string with current username"""
        current = self.db_handler.get_current_user_nick()
        return current

    def get_autosave_opt(self) -> bool:
        """Get autosave option

        return:
            True - enabled

            False - disabled"""
        return self.__autosave

    def __on_closing(self):
        if self.__autosave and self.__game_flag:
            self.__save_cur_game()

        # closing connection to db explicitly just in case
        self.db_handler.close()
        self.destroy()

    def __save_cur_game(self):
        # to save only light mode data
        if self.__dark_theme_fl:
            self.__set_theme(self.BASE_COLOR, self.BASE_LETTERS_COLOR, self.BASE_LBL_COLOR, self.BASE_BTN_COLOR)

        colors_letters = {}

        for i in range(self.ROW_AMOUNT):
            for j in range(self.ROW_LENGTH):
                colors_letters[f'lbl{i}{j}'] = f"{self.__labels_dict[f'lbl{i}{j}'].cget('bg')}:" \
                                               f"{self.__labels_dict[f'lbl{i}{j}'].cget('text')}"

        btn, lbl = "", ""
        for key, value in colors_letters.items():
            lbl += f'{key}:{value}|'

        for key, value in self.__buttons_states.items():
            btn += f'{key}:{value}|'

        self.db_handler.save_state(btn, lbl, self.__chosen_word)

    def get_current_theme(self) -> bool:
        """Get current color theme of main wordle window

        return:
            False - light theme

            True - dark theme"""
        return self.__dark_theme_fl

    def change_color_theme(self):
        """Change color theme and it's flag to opposite in main wordle window"""
        if self.__dark_theme_fl:
            self.__set_theme(self.BASE_COLOR, self.BASE_LETTERS_COLOR, self.BASE_LBL_COLOR, self.BASE_BTN_COLOR)
        else:
            self.__set_theme(self.DT_BASE_COLOR, self.PAINTED_LETTERS_COLOR, self.DT_LBL_COLOR, self.DT_BTN_COLOR)

        self.__dark_theme_fl = not self.__dark_theme_fl

    def __set_theme(self, bg_color: str, ltr_color: str, lbl_color: str, btn_color: str):
        for i, item in enumerate(self.__labels_dict.values()):
            if i < self.__label_pointer:
                continue

            item.config(bg=lbl_color, fg=ltr_color)

        if self.__dark_theme_fl:
            for letter, state in self.__buttons_states.items():
                btn_name = self.__letter_to_button_name_dict[letter]
                color = self.__state_to_color_dict[state]
                self.__btn_dict[btn_name].config(bg=color, fg=ltr_color)
        else:
            for letter, state in self.__buttons_states.items():
                btn_name = self.__letter_to_button_name_dict[letter]
                color = self.__dt_state_to_color_dict[state]
                self.__btn_dict[btn_name].config(bg=color, fg=ltr_color)

        self.config(bg=bg_color)
        self.__menu_frame_left.config(bg=bg_color)
        self.__menu_frame_right.config(bg=bg_color)
        self.__gfield_frame.config(bg=bg_color)
        self.__keyboard_frame.config(bg=bg_color)
        self.__messages_frame.config(bg=bg_color)

        self.__message_label.config(bg=bg_color, fg=ltr_color)
        self.__enter_button.config(bg=btn_color, fg=ltr_color)
        self.__clear_button.config(bg=btn_color, fg=ltr_color)
        self.__stat_button.config(bg=btn_color, fg=ltr_color)
        self.__settings_button.config(bg=btn_color, fg=ltr_color)
        self.__ng_button.config(bg=btn_color, fg=ltr_color)
        self.__profile_button.config(bg=btn_color, fg=ltr_color)

    @staticmethod
    def center_window(window, w_width: int, w_height: int):
        """Centers tk window in the middle of the screen

        params:
            window - tk based window

            w_width - width of window

            w_length - height of window"""
        x = window.winfo_screenwidth() // 2 - w_width // 2
        y = window.winfo_screenheight() // 2 - w_height // 2
        window.geometry(f"{w_width}x{w_height}+{x}+{y}")

    def __root_setup(self):
        self.title("Wordle")
        self.center_window(self, self.__window_width, self.__window_length)
        self.minsize(width=self.__window_width, height=self.__window_length)

        # lets root to fill all remaining space, so main frame will always be centered
        self.grid_columnconfigure(0, weight=1)

        # Allowing typing letters from keyboard
        eng_keyboard = list("qwertyuiop[]asdfghjkl;'`zxcvbnm,.")
        for i in range(33):
            self.bind(
                eng_keyboard[i],
                lambda event, ru_ltr=self.__alphabet[self.__numerical_keyboard[i]].upper(): self.__button_click(ru_ltr)
            )
        # for Caps Lock
        for i in range(33):
            self.bind(
                eng_keyboard[i].upper(),
                lambda event, ru_ltr=self.__alphabet[self.__numerical_keyboard[i]].upper(): self.__button_click(ru_ltr)
            )

        self.bind("<BackSpace>", lambda event: self.__clear())
        self.bind("<Return>", lambda event: self.__enter())

    def __init_labels(self):
        for i in range(self.ROW_AMOUNT):
            for j in range(self.ROW_LENGTH):
                self.__labels_dict[f'lbl{i}{j}'] = Label(
                    self.__gfield_frame, font=('Arial bold', 20), background='white',
                    width=60, height=60, image=self.__image, compound='center',
                    textvariable=self.__text_vars[self.ROW_LENGTH * i + j]
                )

        self.__message_label = Label(
            self.__messages_frame, width=100, height=2, textvariable=self.__message_label_var,
            font=('Arial', 10)
        )

    def __init_buttons(self):
        for i in range(33):
            letter = self.__alphabet[i].upper()

            self.__btn_dict[f"btn{i}"] = Button(
                self.__keyboard_frame, text=letter, font=("Arial bold", 11),
                command=lambda a=letter: self.__button_click(a)
            )

        self.__clear_button = Button(
            self.__keyboard_frame, text="Очистить", font=("Arial bold", 11), command=self.__clear
        )
        self.__enter_button = Button(
            self.__keyboard_frame, text="Ввод ", font=("Arial bold", 11), command=self.__enter
        )

        # menu frame
        self.__profile_button = Button(
            self.__menu_frame_left, height=1, width=5, text="Профили", command=self.__show_profile
        )
        self.__ng_button = Button(
            self.__menu_frame_left, height=1, width=5, text="Заново", command=self.__new_game
        )
        self.__stat_button = Button(
            self.__menu_frame_right, height=1, width=5, text="Статистика", command=self.__show_stats
        )
        self.__settings_button = Button(
            self.__menu_frame_right, height=1, width=5, text="Параметры", command=self.__show_settings
        )

    # seems like ctrl+c ctrl+v, but im not sure that i should have
    # 1 func and pass params to it to create windows rather that
    # have several distinct funcs, one for each window, even though they are similar
    def __show_profile(self):
        width, length = 400, 500
        p_window = Profiles(width, length, self)
        self.center_window(p_window, width, length)

        # lock root window
        p_window.grab_set()

    def __show_settings(self):
        width, length = 400, 300
        set_window = Settings(width, length, self)
        self.center_window(set_window, width, length)

        # lock root window
        set_window.grab_set()

    def __show_stats(self):
        width, length = 400, 500
        st_window = Statistics(width, length, self)
        self.center_window(st_window, width, length)

        # lock root window
        st_window.grab_set()

    def __place_frames(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=5)

        self.__menu_frame_left.grid(row=0, sticky="NW")
        self.__menu_frame_right.grid(row=0, sticky="NE")

        self.__gfield_frame.grid(sticky="NS")
        self.__messages_frame.grid(sticky="S")
        self.__keyboard_frame.grid(sticky="S")

    def __place_labels(self):
        for i in range(self.ROW_AMOUNT):
            for j in range(self.ROW_LENGTH):
                self.__labels_dict[f'lbl{i}{j}'].grid(column=j, row=i, padx=10, pady=10)

        self.__message_label.grid()

    def __place_buttons(self):
        # keyboard frame
        # one button = 2 colons as default
        for i in range(0, 48, 2):
            self.__btn_dict[f"btn{self.__numerical_keyboard[i // 2]}"].grid(
                padx=10, pady=10, ipadx=10, ipady=10, column=i % 24, row=i // 24, columnspan=2
            )
        self.__enter_button.grid(padx=10, pady=10, ipadx=10, ipady=10, column=0, row=2, columnspan=3, sticky='W')

        for i in range(50, 68, 2):
            self.__btn_dict[f"btn{self.__numerical_keyboard[i // 2 - 1]}"].grid(
                padx=10, pady=10, ipadx=10, ipady=10, column=i % 24 + 1, row=i // 24, columnspan=2
            )
        self.__clear_button.grid(padx=10, pady=10, ipadx=10, ipady=10, column=21, row=2, columnspan=3, sticky='E')

        # menu frame
        self.__ng_button.grid(ipadx=20, ipady=5, column=0, row=0)
        self.__stat_button.grid(ipadx=20, ipady=5, column=0, row=0)
        self.__settings_button.grid(ipadx=20, ipady=5, column=1, row=0)
        self.__profile_button.grid(ipadx=20, ipady=5, column=1, row=0)

    @staticmethod
    def __to_dict(word: Union[list, str]) -> dict:
        s = {}
        for i, item in enumerate(word):
            if item not in s.keys():
                s[item] = []
                s[item].append(i)
            else:
                s[item].append(i)

        return s

    def __alg_cmp(self, a: Union[list, str], b: Union[list, str]) -> list[int]:
        """
        :param a: hidden word
        :param b: input word
        :return: state
        """
        # that shit works
        s = [1 for _ in range(len(a))]
        a_dict = self.__to_dict(a)
        b_dict = self.__to_dict(b)
        d = []
        for key, value in b_dict.items():
            # looking for all 3s:
            if key in a_dict.keys():
                for b_item in value:
                    if b_item in a_dict[key]:
                        s[b_item] = 3
                        d.append(b_item)

                for item in d:
                    a_dict[key].remove(item)
                    b_dict[key].remove(item)

                d = []

                # looking for all 2s:
                if not b_dict[key]:
                    continue
                else:
                    a_i = len(a_dict[key])
                    b_i = len(b_dict[key])
                    i = 0
                    while min(a_i, b_i) > 0:
                        s[b_dict[key][i]] = 2
                        i += 1
                        b_i -= 1
                        a_i -= 1

        return s

    def __paint_row(self, states: list):
        i = self.__label_pointer // self.ROW_LENGTH - 1
        for j in range(len(states)):
            state = states[j]
            color = self.__state_to_color_dict[state]
            self.__labels_dict[f"lbl{i}{j}"].config(bg=color, fg=self.PAINTED_LETTERS_COLOR)

    def __unlock_next_row(self):
        # increment coefficient for allowing typing in the next row
        # and disallowing erasing previous one
        self.__cur_row += 1

    def __paint_keyboard_letters(self, states: list[int]):
        # creating better representation of states
        # which shows it in a way: letter: state
        # since higher states override lower ones
        # for the same letter
        st_dict = {}
        for i, item in enumerate(self.__input_word):
            if item not in st_dict.keys():
                st_dict[item] = states[i]
            elif st_dict[item] < states[i]:
                st_dict[item] = states[i]

        # changing button_states dict
        # 0 - not pressed, always to be overridden
        # 1 - grey letter, not presented in the word, never to be overridden
        # 2 - yellow letter, presented, but in the wrong place, may be overridden only by green state (3)
        # 3 - green letter, presented in the word, in the exact place, never to be overridden
        for letter, state in st_dict.items():
            letter = letter.lower()
            if self.__buttons_states[letter] == 0:
                self.__buttons_states[letter] = state
            elif self.__buttons_states[letter] == 2:
                if state == 3:
                    self.__buttons_states[letter] = 3

            # now to reconfigure button color
            if self.__dark_theme_fl:
                abs_state = self.__buttons_states[letter]
                color = self.__dt_state_to_color_dict[abs_state]
                btn_name = self.__letter_to_button_name_dict[letter]
                self.__btn_dict[btn_name].configure(bg=color)
            else:
                abs_state = self.__buttons_states[letter]
                color = self.__state_to_color_dict[abs_state]
                btn_name = self.__letter_to_button_name_dict[letter]
                self.__btn_dict[btn_name].configure(bg=color)

    def __valid_word(self):
        # comparing words
        states = self.__alg_cmp(self.__chosen_word, self.__input_word)
        print(f'chosen | guess: {self.__chosen_word} | {"".join(self.__input_word)}')

        # painting everything
        self.__paint_row(states)
        self.__paint_keyboard_letters(states)

        # checking whether its a win, a loss, or to proceed to the next row
        if states == [3, 3, 3, 3, 3]:
            self.__congratulate()
        elif self.__cur_row == 6:
            self.__game_over()
        else:
            self.__unlock_next_row()

    def __check_full_row(self):
        if self.__label_pointer == 0:
            return False

        if self.__label_pointer % self.ROW_LENGTH == 0 and self.__cur_row == self.__label_pointer // self.ROW_LENGTH:
            return True
        return False

    def __check_word_in_dict(self):
        word = ''.join(self.__input_word).lower()
        if word in self.__words_list:
            return True
        return False

    def __get_input_word(self):
        for i in range((self.__cur_row - 1) * self.ROW_LENGTH, self.__cur_row * self.ROW_LENGTH):
            self.__input_word[i % self.ROW_LENGTH] = self.__text_vars[i].get()

    def __enter(self):
        if self.__game_flag:
            # if current row is not full
            if not self.__check_full_row():
                self.__message_label_var.set('Мало букв')
            else:
                self.__get_input_word()

                # if row is full, but word is not valid
                if not self.__check_word_in_dict():
                    self.__message_label_var.set('Такого слова нет в словаре')

                # if row is full and word is valid
                else:
                    self.__valid_word()

    def __clear(self):
        if self.__game_flag:
            # clearing message label
            self.__message_label_var.set('')

            # Checking if its allowed to erase
            # (label pointer points at label within range + 1 of current row)
            if (self.__cur_row - 1) * self.ROW_LENGTH < self.__label_pointer <= self.__cur_row * self.ROW_LENGTH:
                # clearing single letter label
                current = self.__label_pointer - 1
                self.__text_vars[current].set('')

                # decrementing label pointer
                self.__label_pointer -= 1

    def __button_click(self, letter: str):
        if self.__game_flag:
            # erase message in message label
            self.__message_label_var.set('')

            # checking whether its allowed to type in the next row
            if self.__label_pointer < self.__cur_row * 5:
                # putting letter in the label
                self.__text_vars[self.__label_pointer].set(letter)

                # incrementing label pointer
                self.__label_pointer += 1

    def __re_init_labels(self):
        for item in self.__text_vars:
            item.set('')

        if self.__dark_theme_fl:
            bg_color = self.DT_LBL_COLOR
            ltr_color = self.DT_LETTERS_COLOR
        else:
            bg_color = self.BASE_LBL_COLOR
            ltr_color = self.BASE_LETTERS_COLOR

        for item in self.__labels_dict.values():
            item.config(bg=bg_color, fg=ltr_color)

        self.__message_label_var.set('')

    def __re_init_buttons(self):
        if self.__dark_theme_fl:
            bg_color = self.DT_BTN_COLOR
            ltr_color = self.DT_LETTERS_COLOR
        else:
            bg_color = self.BASE_BTN_COLOR
            ltr_color = self.BASE_LETTERS_COLOR

        for item in self.__btn_dict.values():
            item.config(bg=bg_color, fg=ltr_color)

    def __congratulate(self):
        # deleting last game
        self.db_handler.add_win(self.__cur_row)

        self.db_handler.save_state("", "", "")
        self.__message_label_var.set(f'Поздраляю! Загадано было слово: {self.__chosen_word}\nДля начала новой игры '
                                     f'нажмите кнопку "заново".')
        self.__game_flag = False

    def __new_game(self):
        # resetting game variables
        self.__game_flag = True
        self.__label_pointer = 0
        self.__chosen_word = sample(self.__words_list, 1)[0].upper()
        self.__cur_row = 1
        self.__buttons_states = dict.fromkeys(self.__alphabet, 0)

        # clear labels
        self.__re_init_labels()

        # clear buttons colors
        self.__re_init_buttons()

        # deleting last game
        self.db_handler.save_state("", "", "")

    def __game_over(self):
        self.db_handler.add_loss()
        self.__message_label_var.set(f'Какая жалость! Загадано было слово: {self.__chosen_word}\nДля начала новой игры '
                                     f'нажмите кнопку "Заново".')
        self.__game_flag = False

    def run(self):
        """Run app"""
        self.mainloop()


class Statistics(Toplevel):
    """Statistics window"""
    def __init__(self, width: int, length: int, root: Wordle):
        super().__init__(root)
        self.root: Wordle = root
        self.title("Статистика")
        self.grid_columnconfigure(0, weight=1)
        self.minsize(width=width, height=length)
        self.resizable(False, False)

        self.__data: dict = self.__get_data()

        # colors
        self.BASE_COLOR: str = '#f0f0f0'
        self.DT_BASE_COLOR: str = '#121212'

        self.BASE_LETTERS_COLOR: str = 'black'
        self.DT_LETTERS_COLOR: str = '#F6F6F6'

        self.BASE_BAR_COLOR: str = '#959595'
        self.DT_BAR_COLOR: str = '#656565'

        # frames
        self.__upper_frame: Frame = Frame(self)
        self.__lower_frame: Frame = Frame(self)

        # upper frame labels and vars
        self.__upper_head_lbl: Label = Label(self.__upper_frame, text="СТАТИСТИКА", font=("Arial bold", 18))

        # 0 - 2 columns
        self.__g_played_number_var: StringVar = StringVar()
        self.__g_played_number_var.set(f"{self.__data['played']}")
        self.__g_played_number_lbl: Label = Label(
            self.__upper_frame, font=("Arial bold", 18), textvariable=self.__g_played_number_var
        )
        self.__g_played_text_lbl: Label = Label(self.__upper_frame, text="Сыграно")

        # 3 - 5 columns
        self.__winrate_number_var: StringVar = StringVar()
        if self.__data['played'] == 0:
            self.__winrate_number_var.set("0")
        else:
            self.__winrate_number_var.set(
                f"{round((self.__data['games_won'] / self.__data['played']) * 100)}"
            )

        self.__winrate_number_lbl: Label = Label(
            self.__upper_frame, font=("Arial bold", 18), textvariable=self.__winrate_number_var
        )
        self.__winrate_text_lbl: Label = Label(self.__upper_frame, text="% побед")

        # 6 - 8 columns
        self.__cur_streak_number_var: StringVar = StringVar()
        self.__cur_streak_number_var.set(f'{self.__data["current_streak"]}')
        self.__cur_streak_number_lbl: Label = Label(
            self.__upper_frame, font=("Arial bold", 18), textvariable=self.__cur_streak_number_var
        )
        self.__cur_streak_text_lbl: Label = Label(self.__upper_frame, text="Тек. серия\nпобед")

        # 9 - 11 columns
        self.__max_streak_number_var: StringVar = StringVar()
        self.__max_streak_number_var.set(f'{self.__data["max_streak"]}')
        self.__max_streak_number_lbl: Label = Label(
            self.__upper_frame, font=("Arial bold", 18), textvariable=self.__max_streak_number_var
        )
        self.__max_streak_text_lbl: Label = Label(self.__upper_frame, text="Макс.серия\nпобед")

        # lower frame labels and vars
        self.__lower_head_lbl: Label = Label(self.__lower_frame, text="РАСПРЕДЕЛЕНИЕ ПОПЫТОК", font=("Arial bold", 18))
        self.__barchart_canvas: Canvas = self.__make_barchart()

        self.__place_upper_frame_and_labels()
        self.__place_lower_frame_and_labels()
        self.__bind_keys()
        self.set_theme()

    def __get_data(self) -> dict:
        raw = self.root.db_handler.get_current_user()
        if not raw:
            raw = ['Dummy', None, 7, 7, 7, 7, 7, 1, 2, 5, 8, 3, 1]

        # mighty unpacking
        d = {
            "nick": raw[0], "played": raw[2], "games_won": raw[3], "games_lost": raw[4],
            "current_streak": raw[5], "max_streak": raw[6], "first_try": raw[7],
            "second_try": raw[8], "third_try": raw[9], "fourth_try": raw[10],
            "fifth_try": raw[11], "sixth_try": raw[12]
        }
        return d

    def set_theme(self):
        dark = self.root.get_current_theme()
        if dark:
            self.__set_theme(self.DT_BASE_COLOR, self.DT_LETTERS_COLOR)
        else:
            self.__set_theme(self.BASE_COLOR, self.BASE_LETTERS_COLOR)

    def __bind_keys(self):
        self.bind("<Escape>", lambda event: self.destroy())

    def __place_upper_frame_and_labels(self):
        # 12 columns, 3 rows
        self.__upper_frame.grid(row=0, column=0, padx=10, pady=10)

        self.__upper_head_lbl.grid(row=0, column=0, columnspan=12, padx=60, pady=15)

        self.__g_played_number_lbl.grid(row=1, column=0, columnspan=3, padx=10, pady=3)
        self.__g_played_text_lbl.grid(row=2, column=0, columnspan=3, padx=10)

        self.__winrate_number_lbl.grid(row=1, column=3, columnspan=3, padx=10, pady=3)
        self.__winrate_text_lbl.grid(row=2, column=3, columnspan=3, padx=10)

        self.__cur_streak_number_lbl.grid(row=1, column=6, columnspan=3, padx=10, pady=3)
        self.__cur_streak_text_lbl.grid(row=2, column=6, columnspan=3, padx=10)

        self.__max_streak_number_lbl.grid(row=1, column=9, columnspan=3, padx=10, pady=3)
        self.__max_streak_text_lbl.grid(row=2, column=9, columnspan=3, padx=10)

    def __place_lower_frame_and_labels(self):
        self.__lower_frame.grid(row=1, column=0, padx=10, pady=10)
        self.__lower_frame.grid_columnconfigure(0, weight=1)
        self.__lower_head_lbl.grid(row=0, padx=10, pady=10)
        self.__barchart_canvas.grid(row=1)

    def __make_barchart(self) -> Canvas:
        # checking current theme
        dark = self.root.get_current_theme()
        if dark:
            bg = self.DT_BASE_COLOR
            bbc = self.DT_BAR_COLOR
            txt = self.DT_LETTERS_COLOR
        else:
            bg = self.BASE_COLOR
            bbc = self.BASE_BAR_COLOR
            txt = self.BASE_LETTERS_COLOR

        # the Figure class represents the drawing area on which matplotlib charts will be drawn
        figure = Figure(figsize=(2.5, 2.5), dpi=100)
        figure.patch.set_facecolor(bg)

        # the FigureCanvasTkAgg connects the Figure object with a Tkinter’s Canvas object
        figure_canvas = FigureCanvasTkAgg(figure, self.__lower_frame)

        # adding a subplot to the figure and returning the axes of the subplot
        axes = figure.add_subplot()

        # data for bars
        attempts = [i for i in range(1, 7)]
        scores = [self.__data["first_try"], self.__data["second_try"], self.__data["third_try"],
                  self.__data["fourth_try"], self.__data["fifth_try"], self.__data["sixth_try"]]

        bars = axes.barh(attempts, scores, color=bbc)

        axes.set_facecolor(bg)
        axes.invert_yaxis()

        # remove x axis
        axes.get_xaxis().set_visible(False)

        # remove borders
        axes.spines['top'].set_visible(False)
        axes.spines['bottom'].set_visible(False)
        axes.spines['right'].set_visible(False)
        axes.spines['left'].set_visible(False)

        axes.set_yticks(attempts)
        axes.tick_params(labelcolor=txt)

        # put values on the right of the bars
        for bar in bars:
            width = bar.get_width()
            label_y = bar.get_y() + bar.get_height() / 1.5
            if width > 0:
                axes.text(width, label_y, s=f'{width}', color=txt)

        return figure_canvas.get_tk_widget()

    def __set_theme(self, bg_color: str, txt_color: str):
        self.config(bg=bg_color)

        self.__upper_frame.config(bg=bg_color)
        self.__lower_frame.config(bg=bg_color)

        self.__upper_head_lbl.config(bg=bg_color, fg=txt_color)
        self.__lower_head_lbl.config(bg=bg_color, fg=txt_color)

        self.__g_played_number_lbl.config(bg=bg_color, fg=txt_color)
        self.__g_played_text_lbl.config(bg=bg_color, fg=txt_color)
        self.__winrate_number_lbl.config(bg=bg_color, fg=txt_color)
        self.__winrate_text_lbl.config(bg=bg_color, fg=txt_color)
        self.__cur_streak_number_lbl.config(bg=bg_color, fg=txt_color)
        self.__cur_streak_text_lbl.config(bg=bg_color, fg=txt_color)
        self.__max_streak_number_lbl.config(bg=bg_color, fg=txt_color)
        self.__max_streak_text_lbl.config(bg=bg_color, fg=txt_color)

        self.__barchart_canvas.config(bg=bg_color)


class Settings(Toplevel):
    """Settings window"""
    def __init__(self, width: int, length: int, root: Optional[Wordle] = None):
        super().__init__(root)
        self.root: Optional[Wordle] = root
        self.title("Настройки")
        self.minsize(width=width, height=length)
        self.resizable(False, False)
        self.grid_columnconfigure(0, weight=1)

        # colors
        self.BASE_COLOR: str = '#f0f0f0'
        self.DT_BASE_COLOR: str = '#121212'

        self.BASE_LETTERS_COLOR: str = 'black'
        self.DT_LETTERS_COLOR: str = 'grey'

        self.__frame: Frame = Frame(self)

        self.__autosave_button = Checkbutton(
            self.__frame, text="Автосохранение", font=("Arial bold", 15), command=self.__switch_autosave
        )

        if self.root.get_autosave_opt():
            self.__autosave_button.select()

        self.__dark_theme_button = Checkbutton(
            self.__frame, text="Темный режим", font=("Arial bold", 15), command=self.__switch_theme
        )

        self.__place()
        self.__bind_keys()
        self.set_theme()

    def __switch_autosave(self):
        self.root.change_autosave()

    def set_theme(self):
        dark = self.root.get_current_theme()
        if dark:
            self.__set_theme(self.DT_BASE_COLOR, self.DT_LETTERS_COLOR)
        else:
            self.__set_theme(self.BASE_COLOR, self.BASE_LETTERS_COLOR)

    def __switch_theme(self):
        self.root.change_color_theme()
        self.set_theme()

    def __bind_keys(self):
        self.bind("<Escape>", lambda event: self.destroy())

    def __place(self):
        self.__frame.grid(padx=10, pady=10)
        self.__dark_theme_button.grid(row=0, sticky="W")
        self.__autosave_button.grid(row=1, sticky="W")

    def __set_theme(self, bg_color: str, txt_color: str):
        self.config(bg=bg_color)
        self.__frame.config(bg=bg_color)
        self.__dark_theme_button.config(bg=bg_color, activebackground=bg_color, fg=txt_color)
        self.__autosave_button.config(bg=bg_color, activebackground=bg_color, fg=txt_color)


class Profiles(Toplevel):
    """Profiles window"""
    def __init__(self, width: int, length: int, root: Optional[Wordle] = None):
        super().__init__(root)
        self.root: Optional[Wordle] = root
        self.title("Профили")
        self.minsize(width=width, height=length)
        self.resizable(False, False)
        self.grid_columnconfigure(0, weight=1)

        # colors
        self.BASE_COLOR: str = '#f0f0f0'
        self.DT_BASE_COLOR: str = '#121212'

        self.BASE_LETTERS_COLOR: str = 'black'
        self.DT_LETTERS_COLOR: str = '#F6F6F6'

        self.BASE_LBL_COLOR: str = '#f0f0f0'
        self.DT_LBL_COLOR: str = '#121212'

        self.BASE_BTN_COLOR: str = '#f0f0f0'
        self.DT_BTN_COLOR: str = 'grey'

        self.CURRENT_PROFILE: str = '#5EA83D'

        self.__frame: Frame = Frame(self)
        self.__btn_frame: Frame = Frame(self.__frame)
        self.__btn_frame.grid_columnconfigure(0, weight=1)
        self.__btn_frame.grid_columnconfigure(1, weight=4)
        self.__btn_frame.grid_columnconfigure(2, weight=1)

        self.__head_label: Label = Label(self.__frame, text="ПРОФИЛИ", font=("Arial bold", 20))

        self.__profiles_canvas: Canvas = Canvas(self.__frame, width=300, height=200)

        self.__prof_scrollbar: Scrollbar = Scrollbar(
            self.__frame, orient=VERTICAL, command=self.__profiles_canvas.yview
        )

        # bind canvas and scroll bar together
        self.__profiles_canvas.config(yscrollcommand=self.__prof_scrollbar.set)
        self.__profiles_canvas.bind(
            "<Configure>", lambda event: self.__profiles_canvas.configure(
                scrollregion=self.__profiles_canvas.bbox("all")
            )
        )

        # set and bind a container for canvas to put shit inside it
        self.__canvas_frame: Frame = Frame(self.__profiles_canvas)
        self.__canvas_frame_id: int = self.__profiles_canvas.create_window(
            (0, 0), window=self.__canvas_frame, anchor="nw"
        )

        self.__p_add_button: Button = Button(self.__btn_frame, text="Создать", command=self.__add_profile)

        self.update_profiles()

        self.__place()
        self.set_theme()

    def __choose(self, p_name: str):
        """Mark provided username as current in db"""
        current = self.root.get_current_user()
        if current:
            self.root.db_handler.unset_current_user(current)

        self.root.db_handler.set_current_user(p_name)

        self.update_profiles()

    def __delete(self, p_name: str):
        """Delete provided username from db"""
        really = askokcancel(
            title="Confirmation",
            message=f"Вы точно хотите удалить пользователя {p_name}?",
            icon=WARNING
        )

        if really:
            self.root.db_handler.delete_user(p_name)
            self.update_profiles()

    def __clear_canvas(self):
        for item in self.__canvas_frame.winfo_children():
            self.__canvas_frame.nametowidget(item).destroy()

    def update_profiles(self):
        """Updates profile canvas: clear->fill in with updated data"""
        # clear canvas
        self.__clear_canvas()
        current = self.root.get_current_user()

        # get and apply current theme
        dark = self.root.get_current_theme()
        if dark:
            lbl_color = self.DT_LBL_COLOR
            btn_color = self.DT_BTN_COLOR
            txt_color = self.DT_LETTERS_COLOR
        else:
            lbl_color = self.BASE_LBL_COLOR
            btn_color = self.BASE_BTN_COLOR
            txt_color = self.BASE_LETTERS_COLOR

        # fill canvas with profiles
        p = self.__get_profiles()
        for i, profile in enumerate(p):
            if profile == current:
                Label(
                    self.__canvas_frame, name=f"label{i}", text=profile, bg=self.CURRENT_PROFILE, fg=txt_color
                ).grid(row=i, column=0, columnspan=2, pady=5, sticky="W")
            else:
                Label(
                    self.__canvas_frame, name=f"label{i}", text=profile, bg=lbl_color, fg=txt_color
                ).grid(row=i, column=0, columnspan=2, pady=5, sticky="W")

            Button(
                self.__canvas_frame, name=f"btn_ch{i}", text="Выбрать", command=lambda a=profile: self.__choose(a),
                bg=btn_color, fg=txt_color
            ).grid(row=i, column=2, pady=5, padx=50, sticky="E")

            Button(
                self.__canvas_frame, name=f"btn_del{i}", text="Удалить", command=lambda a=profile: self.__delete(a),
                bg=btn_color, fg=txt_color
            ).grid(row=i, column=3, pady=5, sticky="E")

    def __add_profile(self):
        """Create new window to add new profile"""
        width, length = 300, 80
        p_window = ProfileGetterWindow(width, length, self)
        self.root.center_window(p_window, width, length)

        p_window.grab_set()

    def __get_profiles(self) -> list[str]:
        users_raw = self.root.db_handler.get_users()
        users = [item[1] for item in users_raw]
        return users

    def __place(self):
        self.__frame.grid(padx=10, pady=10)
        self.__head_label.grid(row=0, column=0, padx=10, pady=10)
        self.__profiles_canvas.grid(row=1, column=0)
        self.__prof_scrollbar.grid(row=1, column=1, sticky="NS")
        self.__btn_frame.grid(row=2, sticky='EW')
        self.__p_add_button.grid(row=0, column=0, pady=10, sticky="W")

    def set_theme(self):
        dark = self.root.get_current_theme()
        if dark:
            self.__set_theme(self.DT_BASE_COLOR, self.DT_LETTERS_COLOR, self.DT_LBL_COLOR, self.DT_BTN_COLOR)
        else:
            self.__set_theme(self.BASE_COLOR, self.BASE_LETTERS_COLOR, self.BASE_LBL_COLOR, self.BASE_BTN_COLOR)

    def __set_theme(self, bg_color: str, txt_color: str, lbl_color: str, btn_color: str):
        self.config(bg=bg_color)
        self.__frame.config(bg=bg_color)
        self.__btn_frame.config(bg=bg_color)
        self.__profiles_canvas.config(bg=bg_color)
        self.__canvas_frame.config(bg=bg_color)
        self.__head_label.config(bg=lbl_color, fg=txt_color)
        self.__p_add_button.config(bg=btn_color, fg=txt_color)


class ProfileGetterWindow(Toplevel):
    """Window for getting new profile"""
    def __init__(self, width: int, length: int, root):
        super().__init__(root)
        self.root = root
        self.title("Создание профиля")
        self.minsize(width=width, height=length)
        self.resizable(False, False)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)

        # nick lengths
        self.MIN_NICK_LENGTH = 4
        self.MAX_NICK_LENGTH = 24

        # colors
        self.BASE_COLOR: str = '#f0f0f0'
        self.DT_BASE_COLOR: str = '#121212'

        self.BASE_LETTERS_COLOR: str = 'black'
        self.DT_LETTERS_COLOR: str = '#F6F6F6'

        self.BASE_LBL_COLOR: str = '#f0f0f0'
        self.DT_LBL_COLOR: str = '#121212'

        self.BASE_BTN_COLOR: str = '#f0f0f0'
        self.DT_BTN_COLOR: str = 'grey'

        # init shit
        self.__label = Label(self, text="Имя профиля:", font=("Arial", 11))
        self.__ok_btn = Button(self, text="Ок", command=self.__add_profile)
        self.__cancel_btn = Button(self, text="Отмена", command=self.__on_closing)
        self.__entry = Entry(self, width=30)
        self.__place()

        self.set_theme()
        self.protocol("WM_DELETE_WINDOW", self.__on_closing)

    def __add_profile(self):
        user_name = self.__entry.get()
        if len(user_name) > self.MAX_NICK_LENGTH:
            showinfo(title='Too many characters', message='Слишком длинное имя профиля')
            return

        elif len(user_name) < self.MIN_NICK_LENGTH:
            showinfo(title='Not enough characters', message='Слишком короткое имя профиля')
            return

        ok = self.root.root.db_handler.add_user(user_name)
        if not ok:
            showinfo(title='Profile duplicate', message='Профиль с таким именем уже существует!')

        self.__on_closing()

    def __on_closing(self):
        self.root.grab_set()
        self.root.update_profiles()
        self.destroy()

    def __place(self):
        self.__label.grid(row=0, column=0, padx=5, pady=10)
        self.__ok_btn.grid(row=1, column=0, ipadx=3, ipady=3)
        self.__cancel_btn.grid(row=1, column=1, ipadx=3, ipady=3)
        self.__entry.grid(row=0, column=1, padx=5, pady=10)

    def set_theme(self):
        dark = self.root.root.get_current_theme()
        if dark:
            self.__set_theme(self.DT_BASE_COLOR, self.DT_LETTERS_COLOR, self.DT_LBL_COLOR, self.DT_BTN_COLOR)
        else:
            self.__set_theme(self.BASE_COLOR, self.BASE_LETTERS_COLOR, self.BASE_LBL_COLOR, self.BASE_BTN_COLOR)

    def __set_theme(self, bg_color: str, txt_color: str, lbl_color: str, btn_color: str):
        self.config(bg=bg_color)
        self.__label.config(bg=lbl_color, fg=txt_color)
        self.__ok_btn.config(bg=btn_color, fg=txt_color)
        self.__cancel_btn.config(bg=btn_color, fg=txt_color)
        self.__entry.config(bg=lbl_color, fg=txt_color)


class OkCancelWindow(Toplevel):
    # askokcancel func brings in strange bug
    # of keyboard keybindings stop working for some reason
    # until some action in OS is performed
    def __init__(self, width: int, length: int, root: Wordle):
        super().__init__(root)
        self.root = root
        self.title("Загрузка")
        self.minsize(width=width, height=length)
        self.resizable(False, False)

        self.grid_columnconfigure(1, weight=1)

        self.__lbl = Label(self, text="Загрузить последнюю игру?", font=("Arial bold", 12))
        self.__ok_btn = Button(self, text="Ок", command=self.__ok)
        self.__cancel_btn = Button(self, text="Отмена", command=self.destroy)

        self.__lbl.grid(row=0, column=0, columnspan=3, sticky="NSEW", pady=20)
        self.__ok_btn.grid(row=1, column=0, sticky="W", ipadx=20, padx=10)
        self.__cancel_btn.grid(row=1, column=2, sticky="E", ipadx=10, padx=10)

        self.protocol("WM_DELETE_WINDOW", self.destroy)

    def __ok(self):
        self.root.init_game_data()
        self.destroy()


def main():
    game = Wordle("data.db")
    game.run()


if __name__ == "__main__":
    main()
