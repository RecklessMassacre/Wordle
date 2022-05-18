import sqlite3
from typing import Optional, Union
from tkinter import Tk, Label, Frame, Button, PhotoImage, StringVar, Toplevel, Canvas, Scrollbar, Entry
import tkinter.constants as c
from tkinter.messagebox import showinfo
from random import sample
from os.path import exists
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class DBHandler:
    def __init__(self, db_file):
        if not exists(db_file):
            raise sqlite3.Error("Get that fucking db, all words are inside!")

        self._conn = sqlite3.connect(db_file)
        self._cur = self._conn.cursor()
        self._on_connect()

        if not self.check_db_init():
            self._setup_empty_db()

        print(self.get_current_user_nick())

    # errors cannot occur ... so fuck try except
    def check_db_init(self):
        self._cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        arr = [item for item in self._cur.fetchall()]

        return True if arr else False

    def _setup_empty_db(self):
        self._cur.execute(
            "CREATE TABLE IF NOT EXISTS user (id INTEGER, nick_name TEXT NOT NULL, "
            "is_current INTEGER, PRIMARY KEY (id))"
        )
        self._cur.execute(
            "CREATE TABLE IF NOT EXISTS stats (user_id INTEGER, played INTEGER, games_won INTEGER,"
            "games_lost INTEGER, current_streak INTEGER, max_streak INTEGER, FOREIGN KEY (user_id) "
            "REFERENCES user(id) ON DELETE CASCADE ON UPDATE NO ACTION)"
        )
        self._cur.execute(
            "CREATE TABLE IF NOT EXISTS distribution (user_id INTEGER, first_try INTEGER, second_try INTEGER,"
            "third_try INTEGER, fourth_try INTEGER, fifth_try INTEGER, sixth_try INTEGER, FOREIGN KEY (user_id) "
            "REFERENCES user(id) ON DELETE CASCADE ON UPDATE NO ACTION)"
        )
        self._cur.execute(
            "CREATE TABLE IF NOT EXISTS keyboard_state (user_id INTEGER, k_state_string TEXT, FOREIGN KEY (user_id) "
            "REFERENCES user(id) ON DELETE CASCADE ON UPDATE NO ACTION)"
        )
        self._cur.execute(
            "CREATE TABLE IF NOT EXISTS labels_state (user_id INTEGER, l_state_string TEXT, FOREIGN KEY (user_id) "
            "REFERENCES user(id) ON DELETE CASCADE ON UPDATE NO ACTION)"
        )
        self._cur.execute(
            "CREATE VIEW get_user AS SELECT u.nick_name, u.is_current, s.played, s.games_won, s.games_lost, "
            "s.current_streak, s.max_streak,d.first_try, d.second_try, d.third_try, d.fourth_try, d.fifth_try, "
            "d.sixth_try, ks.k_state_string, ls.l_state_string FROM user u LEFT JOIN stats s on u.id = s.user_id "
            "LEFT JOIN distribution d on u.id = d.user_id LEFT JOIN keyboard_state ks on u.id = ks.user_id "
            "LEFT JOIN labels_state ls on u.id = ls.user_id"
        )
        self._conn.commit()

    def _on_connect(self):
        self._cur.execute("PRAGMA foreign_keys = ON")
        self._conn.commit()

    def unset_current_user(self, nick_name):
        self._cur.execute("UPDATE user set is_current = 0 WHERE nick_name =?", (nick_name, ))
        self._conn.commit()

    def get_current_user_nick(self):
        self._cur.execute("SELECT nick_name FROM user WHERE is_current = 1")
        tarr = self._cur.fetchall()
        if tarr:
            return tarr[0][0]
        else:
            return ''

    def get_current_user(self):
        """
        All stuff for statistics window
        """
        self._cur.execute("SELECT * FROM get_user WHERE is_current = 1")
        tarr = self._cur.fetchall()
        if tarr:
            return tarr[0]
        else:
            return []

    def set_current_user(self, nick_name):
        self._cur.execute("UPDATE user SET is_current = 1 WHERE nick_name = ?", (nick_name, ))
        self._conn.commit()

    def user_exists(self, nick_name):
        self._cur.execute("SELECT nick_name FROM user WHERE nick_name = ?", (nick_name,))

        arr = [item for item in self._cur.fetchall()]

        return True if arr else False

    def delete_user(self, nick_name):
        self._cur.execute("DELETE FROM user WHERE nick_name = ?", (nick_name,))
        self._conn.commit()

        return True

    def add_user(self, nick_name):
        if self.user_exists(nick_name):
            return False

        self._cur.execute("INSERT INTO user (nick_name, is_current) VALUES (?, 0)", (nick_name,))
        self._cur.execute(
            "INSERT INTO stats(user_id, played, games_won, games_lost, current_streak, max_streak)"
            "VALUES (last_insert_rowid(), 0, 0, 0, 0, 0)"
        )
        self._cur.execute(
            "INSERT INTO distribution(user_id, first_try, second_try, third_try, fourth_try, fifth_try, sixth_try)"
            "VALUES (last_insert_rowid(), 0, 0, 0, 0, 0, 0)"
        )
        self._cur.execute('INSERT INTO keyboard_state(user_id, k_state_string) VALUES (last_insert_rowid(), "")')
        self._cur.execute('INSERT INTO labels_state(user_id, l_state_string) VALUES (last_insert_rowid(), "")')

        self._conn.commit()
        return True

    def get_users(self):
        self._cur.execute("SELECT * FROM user")

        arr = self._cur.fetchall()
        return arr

    def get_words(self):
        self._cur.execute("SELECT * FROM words")

        arr = [item[0] for item in self._cur.fetchall()]
        return arr

    def close(self):
        self._conn.close()


class Wordle(Tk):
    # architecture is shit
    def __init__(self, db_name: str):
        super().__init__()
        # sqlite3
        self.db_handler: DBHandler = DBHandler(db_name)

        # current profile:
        self.profile: str = ''

        # root initialization
        self.window_width: int = 820
        self.window_length: int = 820

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
        self.dark_theme_fl: bool = False

        # game data
        self.ROW_AMOUNT: int = 6
        self.row_length: int = 5
        self.words_list: Optional[list[str]] = self.db_handler.get_words()  # all 5-letters words
        self.chosen_word: str = sample(self.words_list, 1)[0].upper()  # word to guess
        self.input_word: list[str] = [str() for _ in range(self.row_length)]
        self.cur_row: int = 1
        self.label_pointer: int = 0
        self.game_flag: bool = True
        # each number is alphabet position and each array position is keyboard position
        self.numerical_keyboard: list[int] = [
            10, 23, 20, 11, 5, 14, 3, 25, 26, 8, 22, 27,
            21, 28, 2, 0, 16, 17, 15, 12, 4, 7, 30, 6,
            32, 24, 18, 13, 9, 19, 29, 1, 31
        ]

        # zero size image, used to make labels quadratic
        self.image: PhotoImage = PhotoImage()

        # frames definition
        # self.main_frame: Frame = Frame(self.root)
        self.gfield_frame: Frame = Frame(self)
        self.menu_frame_left: Frame = Frame(self)
        self.menu_frame_right: Frame = Frame(self)
        self.keyboard_frame: Frame = Frame(self)
        self.messages_frame: Frame = Frame(self)

        # labels and its requirements definition and initialization
        # message label
        self.message_label: Optional[Label] = None
        self.message_label_var: StringVar = StringVar()
        self.message_label_var.set(
            'Привет! Для ввода букв с клавиатуры нужно перевести раскладку на англ.\n'
            'Для ведения статистики нужно создать профиль'
        )

        # game field labels
        self.labels_dict: dict[str, Label] = {}
        self.text_vars: list[StringVar] = [StringVar() for _ in range(self.row_length * self.ROW_AMOUNT)]
        self.init_labels()

        # buttons and its requirements definition and initialization
        self.alphabet: list[str] = [chr(i) for i in range(ord('а'), ord('а') + 6)] + \
                                   [chr(ord('а') + 33)] + \
                                   [chr(i) for i in range(ord('а') + 6, ord('а') + 32)]
        # state: color
        self.state_to_color_dict: dict[int, str] = {
            0: self.BASE_BTN_COLOR, 1: self.GREY, 2: self.YELLOW, 3: self.GREEN
        }
        self.dt_state_to_color_dict: dict[int, str] = {
            0: self.DT_BTN_COLOR, 1: self.DT_GREY, 2: self.YELLOW, 3: self.GREEN
        }
        self.letter_to_button_name_dict: dict[str, str] = {
            y: f'btn{x}' for x, y in enumerate(self.alphabet)
        }  # letter: button name
        self.buttons_states: dict[str, int] = dict.fromkeys(self.alphabet, 0)  # letters are not capital, letter: state
        self.btn_dict: dict[str, Button] = {}  # button name: button object
        self.clear_button: Optional[Button] = None
        self.enter_button: Optional[Button] = None
        self.ng_button: Optional[Button] = None
        self.stat_button: Optional[Button] = None
        self.settings_button: Optional[Button] = None
        self.profile_button: Optional[Button] = None

        self.init_buttons()

        # root setup
        self.root_setup()

        # placing everything
        self.place_frames()
        self.place_labels()
        self.place_buttons()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def set_current_profile(self, p_name):
        self.profile = p_name

    def on_closing(self):
        # TODO
        # save curr data to db

        # closing connection to db explicitly just in case
        self.db_handler.close()
        self.destroy()

    def get_current_theme(self):
        return self.dark_theme_fl

    def change_color_theme(self):
        if self.dark_theme_fl:
            self.set_theme(
                self.BASE_COLOR, self.BASE_LETTERS_COLOR, self.BASE_LBL_COLOR, self.BASE_BTN_COLOR
            )
        else:
            self.set_theme(
                self.DT_BASE_COLOR, self.PAINTED_LETTERS_COLOR, self.DT_LBL_COLOR, self.DT_BTN_COLOR
            )

        self.dark_theme_fl = not self.dark_theme_fl

    def set_theme(self, bg_color, ltr_color, lbl_color, btn_color):
        for i, item in enumerate(self.labels_dict.values()):
            if i < self.label_pointer:
                continue

            item.config(bg=lbl_color, fg=ltr_color)

        if self.dark_theme_fl:
            for letter, state in self.buttons_states.items():
                btn_name = self.letter_to_button_name_dict[letter]
                color = self.state_to_color_dict[state]
                self.btn_dict[btn_name].config(bg=color, fg=ltr_color)
        else:
            for letter, state in self.buttons_states.items():
                btn_name = self.letter_to_button_name_dict[letter]
                color = self.dt_state_to_color_dict[state]
                self.btn_dict[btn_name].config(bg=color, fg=ltr_color)

        self.config(bg=bg_color)
        self.menu_frame_left.config(bg=bg_color)
        self.menu_frame_right.config(bg=bg_color)
        self.gfield_frame.config(bg=bg_color)
        self.keyboard_frame.config(bg=bg_color)
        self.messages_frame.config(bg=bg_color)

        self.message_label.config(bg=bg_color, fg=ltr_color)
        self.enter_button.config(bg=btn_color, fg=ltr_color)
        self.clear_button.config(bg=btn_color, fg=ltr_color)
        self.stat_button.config(bg=btn_color, fg=ltr_color)
        self.settings_button.config(bg=btn_color, fg=ltr_color)
        self.ng_button.config(bg=btn_color, fg=ltr_color)
        self.profile_button.config(bg=btn_color, fg=ltr_color)

    @staticmethod
    def center_window(window, w_width, w_length):
        x = window.winfo_screenwidth() // 2 - w_width // 2
        y = window.winfo_screenheight() // 2 - w_length // 2
        window.geometry(f"{w_width}x{w_length}+{x}+{y}")

    def root_setup(self):
        self.title("Wordle")
        self.center_window(self, self.window_width, self.window_length)
        self.minsize(width=self.window_width, height=self.window_length)

        # lets root to fill all remaining space, so main frame will always be centered
        self.grid_columnconfigure(0, weight=1)

        # Allowing typing letters from keyboard
        eng_keyboard = list("qwertyuiop[]asdfghjkl;'`zxcvbnm,.")
        for i in range(33):
            self.bind(
                eng_keyboard[i],
                lambda event, ru_letter=self.alphabet[self.numerical_keyboard[i]].upper(): self.button_click(ru_letter)
            )
        # for Caps Lock
        for i in range(33):
            self.bind(
                eng_keyboard[i].upper(),
                lambda event, ru_letter=self.alphabet[self.numerical_keyboard[i]].upper(): self.button_click(ru_letter)
            )

        self.bind("<BackSpace>", lambda event: self.clear())
        self.bind("<Return>", lambda event: self.enter())

    def init_labels(self):
        for i in range(self.ROW_AMOUNT):
            for j in range(self.row_length):
                self.labels_dict[f'lbl{i}{j}'] = Label(
                    self.gfield_frame, font=('Arial bold', 20), background='white',
                    width=60, height=60, image=self.image, compound='center',
                    textvariable=self.text_vars[self.row_length * i + j]
                )

        self.message_label = Label(
            self.messages_frame, width=100, height=2, textvariable=self.message_label_var,
            font=('Arial', 10)
        )

    def init_buttons(self):
        for i in range(33):
            letter = self.alphabet[i].upper()

            self.btn_dict[f"btn{i}"] = Button(
                self.keyboard_frame, text=letter, font=("Arial bold", 11),
                command=lambda a=letter: self.button_click(a)  # !!!
            )

        self.clear_button = Button(
            self.keyboard_frame, text="Очистить", font=("Arial bold", 11), command=self.clear
        )
        self.enter_button = Button(
            self.keyboard_frame, text="Ввод ", font=("Arial bold", 11), command=self.enter
        )

        # menu frame
        self.profile_button = Button(
            self.menu_frame_left, height=1, width=5, text="Профили", command=self.show_profile
        )
        self.ng_button = Button(
            self.menu_frame_left, height=1, width=5, text="Заново", command=self.new_game
        )
        self.stat_button = Button(
            self.menu_frame_right, height=1, width=5, text="Статистика", command=self.show_stats
        )
        self.settings_button = Button(
            self.menu_frame_right, height=1, width=5, text="Параметры", command=self.show_settings
        )

    # seems like ctrl+c ctrl+v, but im not sure that i should have
    # 1 func and pass params to it to create windows rather that
    # have several distinct funcs, one for each window, even though they are similar
    def show_profile(self):
        width, length = 400, 500
        p_window = Profiles(width, length, self)
        self.center_window(p_window, width, length)

        # lock root window
        p_window.grab_set()

        # debug shit
        colors = {}
        for i in range(self.ROW_AMOUNT):
            for j in range(self.row_length):
                colors[f'lbl{i}{j}'] = self.labels_dict[f'lbl{i}{j}'].cget("bg")

        print("lbl states: ", colors)
        print("btn states: ", self.buttons_states)

    def show_settings(self):
        width, length = 400, 300
        set_window = Settings(width, length, self)
        self.center_window(set_window, width, length)

        # lock root window
        set_window.grab_set()

    def show_stats(self):
        width, length = 400, 500
        st_window = Statistics(width, length, self)
        self.center_window(st_window, width, length)

        # lock root window
        st_window.grab_set()

    def place_frames(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=5)

        self.menu_frame_left.grid(row=0, sticky="NW")
        self.menu_frame_right.grid(row=0, sticky="NE")

        self.gfield_frame.grid(sticky="NS")
        self.messages_frame.grid(sticky="S")
        self.keyboard_frame.grid(sticky="S")

    def place_labels(self):
        for i in range(self.ROW_AMOUNT):
            for j in range(self.row_length):
                self.labels_dict[f'lbl{i}{j}'].grid(column=j, row=i, padx=10, pady=10)

        self.message_label.grid()

    def place_buttons(self):
        # keyboard frame
        # one button = 2 colons as default
        for i in range(0, 48, 2):
            self.btn_dict[f"btn{self.numerical_keyboard[i // 2]}"].grid(
                padx=10, pady=10, ipadx=10, ipady=10, column=i % 24, row=i // 24, columnspan=2
            )
        self.enter_button.grid(padx=10, pady=10, ipadx=10, ipady=10, column=0, row=2, columnspan=3, sticky='W')

        for i in range(50, 68, 2):
            self.btn_dict[f"btn{self.numerical_keyboard[i // 2 - 1]}"].grid(
                padx=10, pady=10, ipadx=10, ipady=10, column=i % 24 + 1, row=i // 24, columnspan=2
            )
        self.clear_button.grid(padx=10, pady=10, ipadx=10, ipady=10, column=21, row=2, columnspan=3, sticky='E')

        # menu frame
        self.ng_button.grid(ipadx=20, ipady=5, column=0, row=0)
        self.stat_button.grid(ipadx=20, ipady=5, column=0, row=0)
        self.settings_button.grid(ipadx=20, ipady=5, column=1, row=0)
        self.profile_button.grid(ipadx=20, ipady=5, column=1, row=0)

    @staticmethod
    def _to_dict(word: Union[list, str]) -> dict:
        s = {}
        for i, item in enumerate(word):
            if item not in s.keys():
                s[item] = []
                s[item].append(i)
            else:
                s[item].append(i)

        return s

    def alg_cmp(self, a: Union[list, str], b: Union[list, str]) -> list[int]:
        """
        :param a: hidden word
        :param b: input word
        :return: state
        """
        # that shit works
        s = [1 for _ in range(len(a))]
        a_dict = self._to_dict(a)
        b_dict = self._to_dict(b)
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

    def paint_row(self, states: list):
        i = self.label_pointer // self.row_length - 1
        for j in range(len(states)):
            state = states[j]
            color = self.state_to_color_dict[state]
            self.labels_dict[f"lbl{i}{j}"].configure(background=color, fg=self.PAINTED_LETTERS_COLOR)

    def unlock_next_row(self):
        # increment coefficient for allowing typing in the next row
        # and disallowing erasing previous one
        self.cur_row += 1

    def paint_keyboard_letters(self, states: list[int]):
        # creating better representation of states
        # which shows it in a way: letter: state
        # since higher states override lower ones
        # for the same letter
        st_dict = {}
        for i, item in enumerate(self.input_word):
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
            if self.buttons_states[letter] == 0:
                self.buttons_states[letter] = state
            elif self.buttons_states[letter] == 2:
                if state == 3:
                    self.buttons_states[letter] = 3

            # now to reconfigure button color
            abs_state = self.buttons_states[letter]
            color = self.state_to_color_dict[abs_state]
            btn_name = self.letter_to_button_name_dict[letter]
            self.btn_dict[btn_name].configure(bg=color)

    def valid_word(self):
        # comparing words
        states = self.alg_cmp(self.chosen_word, self.input_word)
        print(f'chosen | guess: {self.chosen_word} | {"".join(self.input_word)}')

        # painting everything
        self.paint_row(states)
        self.paint_keyboard_letters(states)

        # checking whether its a win, a loss, or to proceed to the next row
        if states == [3, 3, 3, 3, 3]:
            self.congratulate()
        elif self.cur_row == 6:
            self.game_over()
        else:
            self.unlock_next_row()

    def check_full_row(self):
        if self.label_pointer == 0:
            return False

        if self.label_pointer % self.row_length == 0 and self.cur_row == self.label_pointer // self.row_length:
            return True
        return False

    def check_word_in_dict(self):
        word = ''.join(self.input_word).lower()
        if word in self.words_list:
            return True
        return False

    def get_input_word(self):
        for i in range((self.cur_row - 1) * self.row_length, self.cur_row * self.row_length):
            self.input_word[i % self.row_length] = self.text_vars[i].get()

    def enter(self):
        if self.game_flag:
            # if current row is not full
            if not self.check_full_row():
                self.message_label_var.set('Мало букв')
            else:
                self.get_input_word()

                # if row is full, but word is not valid
                if not self.check_word_in_dict():
                    self.message_label_var.set('Такого слова нет в словаре')

                # if row is full and word is valid
                else:
                    self.valid_word()

    def clear(self):
        if self.game_flag:
            # clearing message label
            self.message_label_var.set('')

            # Checking if its allowed to erase
            # (label pointer points at label within range + 1 of current row)
            if (self.cur_row - 1) * self.row_length < self.label_pointer <= self.cur_row * self.row_length:
                # clearing single letter label
                current = self.label_pointer - 1
                self.text_vars[current].set('')

                # decrementing label pointer
                self.label_pointer -= 1

    def button_click(self, letter: str):
        if self.game_flag:
            # erase message in message label
            self.message_label_var.set('')

            # checking whether its allowed to type in the next row
            if self.label_pointer < self.cur_row * 5:
                # putting letter in the label
                self.text_vars[self.label_pointer].set(letter)

                # incrementing label pointer
                self.label_pointer += 1

    def run(self):
        self.mainloop()

    def congratulate(self):
        self.message_label_var.set(f'Поздраляю! Загадано было слово: {self.chosen_word}\nДля начала новой игры '
                                   f'нажмите кнопку "заново".')
        self.game_flag = False

    def re_init_labels(self):
        for item in self.text_vars:
            item.set('')

        if self.dark_theme_fl:
            bg_color = self.DT_LBL_COLOR
            ltr_color = self.DT_LETTERS_COLOR
        else:
            bg_color = self.BASE_LBL_COLOR
            ltr_color = self.BASE_LETTERS_COLOR

        for item in self.labels_dict.values():
            item.config(bg=bg_color, fg=ltr_color)

        self.message_label_var.set('')

    def re_init_buttons(self):
        if self.dark_theme_fl:
            bg_color = self.DT_BTN_COLOR
            ltr_color = self.DT_LETTERS_COLOR
        else:
            bg_color = self.BASE_BTN_COLOR
            ltr_color = self.BASE_LETTERS_COLOR

        for item in self.btn_dict.values():
            item.config(bg=bg_color, fg=ltr_color)

    def new_game(self):
        # resetting game variables
        self.game_flag = True
        self.label_pointer = 0
        self.chosen_word = sample(self.words_list, 1)[0].upper()
        self.cur_row = 1
        self.buttons_states = dict.fromkeys(self.alphabet, 0)

        # clear labels
        self.re_init_labels()

        # clear buttons colors
        self.re_init_buttons()

    def game_over(self):
        self.message_label_var.set(f'Какая жалость! Загадано было слово: {self.chosen_word}\nДля начала новой игры '
                                   f'нажмите кнопку "Заново".')
        self.game_flag = False


class Statistics(Toplevel):
    def __init__(self, width: int, length: int, root: Optional[Wordle] = None):
        super().__init__(root)
        self.root: Optional[Wordle] = root
        self.title("Статистика")
        self.grid_columnconfigure(0, weight=1)
        self.minsize(width=width, height=length)
        self.resizable(False, False)

        self.data: dict = self.get_data()

        # colors
        self.BASE_COLOR: str = '#f0f0f0'
        self.DT_BASE_COLOR: str = '#121212'

        self.BASE_LETTERS_COLOR: str = 'black'
        self.DT_LETTERS_COLOR: str = '#F6F6F6'

        self.BASE_BAR_COLOR: str = '#959595'
        self.DT_BAR_COLOR: str = '#656565'

        # frames
        self.upper_frame: Frame = Frame(self)
        self.lower_frame: Frame = Frame(self)

        # upper frame labels and vars
        self.upper_head_lbl: Label = Label(self.upper_frame, text="СТАТИСТИКА", font=("Arial bold", 18))

        # 0 - 2 columns
        self.g_played_number_var: StringVar = StringVar()
        self.g_played_number_var.set(f"{self.data['played']}")
        self.g_played_number_lbl: Label = Label(
            self.upper_frame, font=("Arial bold", 18), textvariable=self.g_played_number_var
        )
        self.g_played_text_lbl: Label = Label(self.upper_frame, text="Сыграно")

        # 3 - 5 columns
        self.winrate_number_var: StringVar = StringVar()
        self.winrate_number_var.set(
            f"{round((self.data['games_won'] / self.data['played']) * 100)}"
        )
        self.winrate_number_lbl: Label = Label(
            self.upper_frame, font=("Arial bold", 18), textvariable=self.winrate_number_var
        )
        self.winrate_text_lbl: Label = Label(self.upper_frame, text="% побед")

        # 6 - 8 columns
        self.cur_streak_number_var: StringVar = StringVar()
        self.cur_streak_number_var.set(f'{self.data["current_streak"]}')
        self.cur_streak_number_lbl: Label = Label(
            self.upper_frame, font=("Arial bold", 18), textvariable=self.cur_streak_number_var
        )
        self.cur_streak_text_lbl: Label = Label(self.upper_frame, text="Тек. серия\nпобед")

        # 9 - 11 columns
        self.max_streak_number_var: StringVar = StringVar()
        self.max_streak_number_var.set(f'{self.data["max_streak"]}')
        self.max_streak_number_lbl: Label = Label(
            self.upper_frame, font=("Arial bold", 18), textvariable=self.max_streak_number_var
        )
        self.max_streak_text_lbl: Label = Label(self.upper_frame, text="Макс.серия\nпобед")

        # lower frame labels and vars
        self.lower_head_lbl: Label = Label(self.lower_frame, text="РАСПРЕДЕЛЕНИЕ ПОПЫТОК", font=("Arial bold", 18))
        self.barchart_canvas: Canvas = self.make_barchart()

        self.place_upper_frame_and_labels()
        self.place_lower_frame_and_labels()
        self.bind_keys()
        self.set_theme()

    def get_data(self) -> dict:
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

    def bind_keys(self):
        self.bind("<Escape>", lambda event: self.destroy())

    def place_upper_frame_and_labels(self):
        # 12 columns, 3 rows
        self.upper_frame.grid(row=0, column=0, padx=10, pady=10)

        self.upper_head_lbl.grid(row=0, column=0, columnspan=12, padx=60, pady=15)

        self.g_played_number_lbl.grid(row=1, column=0, columnspan=3, padx=10, pady=3)
        self.g_played_text_lbl.grid(row=2, column=0, columnspan=3, padx=10)

        self.winrate_number_lbl.grid(row=1, column=3, columnspan=3, padx=10, pady=3)
        self.winrate_text_lbl.grid(row=2, column=3, columnspan=3, padx=10)

        self.cur_streak_number_lbl.grid(row=1, column=6, columnspan=3, padx=10, pady=3)
        self.cur_streak_text_lbl.grid(row=2, column=6, columnspan=3, padx=10)

        self.max_streak_number_lbl.grid(row=1, column=9, columnspan=3, padx=10, pady=3)
        self.max_streak_text_lbl.grid(row=2, column=9, columnspan=3, padx=10)

    def place_lower_frame_and_labels(self):
        self.lower_frame.grid(row=1, column=0, padx=10, pady=10)
        self.lower_frame.grid_columnconfigure(0, weight=1)
        self.lower_head_lbl.grid(row=0, padx=10, pady=10)
        self.barchart_canvas.grid(row=1)

    def make_barchart(self) -> Canvas:
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
        figure_canvas = FigureCanvasTkAgg(figure, self.lower_frame)

        # adding a subplot to the figure and returning the axes of the subplot
        axes = figure.add_subplot()

        # data for bars
        attempts = [i for i in range(1, 7)]
        scores = [self.data["first_try"], self.data["second_try"], self.data["third_try"],
                  self.data["fourth_try"], self.data["fifth_try"], self.data["sixth_try"]]

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
        axes.bar_label(bars, color=txt)

        return figure_canvas.get_tk_widget()

    def __set_theme(self, bg_color: str, txt_color: str):
        self.config(bg=bg_color)

        self.upper_frame.config(bg=bg_color)
        self.lower_frame.config(bg=bg_color)

        self.upper_head_lbl.config(bg=bg_color, fg=txt_color)
        self.lower_head_lbl.config(bg=bg_color, fg=txt_color)

        self.g_played_number_lbl.config(bg=bg_color, fg=txt_color)
        self.g_played_text_lbl.config(bg=bg_color, fg=txt_color)
        self.winrate_number_lbl.config(bg=bg_color, fg=txt_color)
        self.winrate_text_lbl.config(bg=bg_color, fg=txt_color)
        self.cur_streak_number_lbl.config(bg=bg_color, fg=txt_color)
        self.cur_streak_text_lbl.config(bg=bg_color, fg=txt_color)
        self.max_streak_number_lbl.config(bg=bg_color, fg=txt_color)
        self.max_streak_text_lbl.config(bg=bg_color, fg=txt_color)

        self.barchart_canvas.config(bg=bg_color)


class Settings(Toplevel):
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

        self.BASE_LETTERS_COLOR: str = 'black'  # seems like default text color is black
        self.DT_LETTERS_COLOR: str = '#F6F6F6'

        self.frame: Frame = Frame(self)

        # switch button images
        self.on: PhotoImage = PhotoImage(file="misc/on1.png")
        self.off: PhotoImage = PhotoImage(file="misc/off.png")

        self.dark_theme_lbl: Label = Label(self.frame, text="Темный режим", font=("Arial bold", 15))
        self.dark_theme_button: Button = Button(
            self.frame, image=self.off, bd=0, command=self.switch_theme
        )

        self.place()
        self.bind_keys()
        self.__set_theme()

    def __set_theme(self):
        dark = self.root.get_current_theme()
        if dark:
            self.set_theme(self.DT_BASE_COLOR, self.DT_LETTERS_COLOR, self.on)
        else:
            self.set_theme(self.BASE_COLOR, self.BASE_LETTERS_COLOR, self.off)

    def switch_theme(self):
        dark = self.root.get_current_theme()
        if dark:
            self.set_theme(self.BASE_COLOR, self.BASE_LETTERS_COLOR, self.off)
        else:
            self.set_theme(self.DT_BASE_COLOR, self.DT_LETTERS_COLOR, self.on)

        self.root.change_color_theme()

    def bind_keys(self):
        self.bind("<Escape>", lambda event: self.destroy())

    def place(self):
        self.frame.grid(padx=10, pady=10)
        self.dark_theme_lbl.grid(row=0, column=0, padx=10, pady=10)
        self.dark_theme_button.grid(row=0, column=1, padx=10, pady=10)

    def set_theme(self, bg_color: str, txt_color: str, img: PhotoImage):
        self.config(bg=bg_color)
        self.frame.config(bg=bg_color)
        self.dark_theme_lbl.config(bg=bg_color, fg=txt_color)
        self.dark_theme_button.config(bg=bg_color, image=img, activebackground=bg_color)


class Profiles(Toplevel):
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

        self.current_user: str = self.get_current_user()

        self.frame: Frame = Frame(self)
        self.btn_frame: Frame = Frame(self.frame)
        self.btn_frame.grid_columnconfigure(0, weight=1)
        self.btn_frame.grid_columnconfigure(1, weight=4)
        self.btn_frame.grid_columnconfigure(2, weight=1)

        self.head_label: Label = Label(self.frame, text="ПРОФИЛИ", font=("Arial bold", 20))

        self.profiles_canvas: Canvas = Canvas(self.frame, width=300, height=200)

        self.prof_scrollbar: Scrollbar = Scrollbar(
            self.frame, orient=c.VERTICAL, command=self.profiles_canvas.yview
        )

        # bind canvas and scroll bar together
        self.profiles_canvas.config(yscrollcommand=self.prof_scrollbar.set)
        self.profiles_canvas.bind(
            "<Configure>", lambda event: self.profiles_canvas.configure(scrollregion=self.profiles_canvas.bbox("all"))
        )

        # set and bind a container for canvas to put shit inside it
        self.canvas_frame: Frame = Frame(self.profiles_canvas)
        self.canvas_frame_id: int = self.profiles_canvas.create_window((0, 0), window=self.canvas_frame, anchor="nw")

        self.p_add_button: Button = Button(self.btn_frame, text="Создать", command=self.add_profile)
        self.upd_button: Button = Button(self.btn_frame, text="Обновить", command=self.update_profiles)

        self.update_profiles()

        self.place()
        self.__set_theme()

    def get_current_user(self):
        current = self.root.db_handler.get_current_user_nick()
        if current:
            return current

        return ""

    def chose_(self, p_name):
        current = self.get_current_user()
        if current:
            self.root.db_handler.unset_current_user(current)

        self.root.db_handler.set_current_user(p_name)

        # TODO
        # mb not needed at all
        self.root.set_current_profile(p_name)

    def delete_(self, p_name):
        self.root.db_handler.delete_user(p_name)

    def clear_canvas(self):
        for item in self.canvas_frame.winfo_children():
            self.canvas_frame.nametowidget(item).destroy()

    def update_profiles(self):
        self.clear_canvas()

        dark = self.root.get_current_theme()
        if dark:
            lbl_color = self.DT_LBL_COLOR
            btn_color = self.DT_BTN_COLOR
            txt_color = self.DT_LETTERS_COLOR
        else:
            lbl_color = self.BASE_LBL_COLOR
            btn_color = self.BASE_BTN_COLOR
            txt_color = self.BASE_LETTERS_COLOR

        p = self.get_profiles()
        for i, profile in enumerate(p):
            Label(
                self.canvas_frame, name=f"label{i}", text=profile, bg=lbl_color, fg=txt_color
            ).grid(row=i, column=0, pady=5, sticky="W")

            Button(
                self.canvas_frame, name=f"btn_ch{i}", text="Выбрать", command=lambda a=profile: self.chose_(a),
                bg=btn_color, fg=txt_color
            ).grid(row=i, column=2, pady=5, sticky="E")

            Button(
                self.canvas_frame, name=f"btn_del{i}", text="Удалить", command=lambda a=profile: self.delete_(a),
                bg=btn_color, fg=txt_color
            ).grid(row=i, column=3, pady=5, sticky="E")

    def add_profile(self):
        width, length = 300, 80
        p_window = ProfileGetterWindow(width, length, self)
        self.root.center_window(p_window, width, length)

        p_window.grab_set()

    def get_profiles(self):
        users_raw = self.root.db_handler.get_users()
        users = [item[1] for item in users_raw]

        return users

    def place(self):
        self.frame.grid(padx=10, pady=10)
        self.head_label.grid(row=0, column=0, padx=10, pady=10)
        self.profiles_canvas.grid(row=1, column=0)

        self.canvas_frame.grid_columnconfigure(1, weight=1, pad=10)

        self.prof_scrollbar.grid(row=1, column=1, sticky="NS")
        self.btn_frame.grid(row=2, sticky='EW')
        self.p_add_button.grid(row=0, column=0, pady=10, sticky="W")
        self.upd_button.grid(row=0, column=2, pady=10, sticky="E")

    def __set_theme(self):
        dark = self.root.get_current_theme()
        if dark:
            self.set_theme(self.DT_BASE_COLOR, self.DT_LETTERS_COLOR, self.DT_LBL_COLOR, self.DT_BTN_COLOR)
        else:
            self.set_theme(self.BASE_COLOR, self.BASE_LETTERS_COLOR, self.BASE_LBL_COLOR, self.BASE_BTN_COLOR)

    def set_theme(self, bg_color: str, txt_color: str, lbl_color: str, btn_color: str):
        self.config(bg=bg_color)
        self.frame.config(bg=bg_color)
        self.btn_frame.config(bg=bg_color)
        self.canvas_frame.config(bg=bg_color)
        self.head_label.config(bg=lbl_color, fg=txt_color)
        self.upd_button.config(bg=btn_color, fg=txt_color)
        self.p_add_button.config(bg=btn_color, fg=txt_color)


class ProfileGetterWindow(Toplevel):
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
        self.label = Label(self, text="Имя профиля:", font=("Arial", 11))
        self.ok_btn = Button(self, text="Ок", command=self.add_profile)
        self.cancel_btn = Button(self, text="Отмена", command=self.on_closing)
        self.entry = Entry(self, width=30)
        self.place()

        self.__set_theme()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def add_profile(self):
        user_name = self.entry.get()
        if len(user_name) > self.MAX_NICK_LENGTH:
            showinfo(title='Too many characters', message='Слишком длинное имя профиля')
            return

        elif len(user_name) < self.MIN_NICK_LENGTH:
            showinfo(title='Not enough characters', message='Слишком короткое имя профиля')
            return

        ok = self.root.root.db_handler.add_user(user_name)  # that's nasty
        if not ok:
            showinfo(title='Profile duplicate', message='Профиль с таким именем уже существует!')

        self.on_closing()

    def on_closing(self):
        self.root.grab_set()
        self.destroy()

    def place(self):
        self.label.grid(row=0, column=0, padx=5, pady=10)
        self.ok_btn.grid(row=1, column=0, ipadx=3, ipady=3)
        self.cancel_btn.grid(row=1, column=1, ipadx=3, ipady=3)
        self.entry.grid(row=0, column=1, padx=5, pady=10)

    def __set_theme(self):
        dark = self.root.root.get_current_theme()
        if dark:
            self.set_theme(self.DT_BASE_COLOR, self.DT_LETTERS_COLOR, self.DT_LBL_COLOR, self.DT_BTN_COLOR)
        else:
            self.set_theme(self.BASE_COLOR, self.BASE_LETTERS_COLOR, self.BASE_LBL_COLOR, self.BASE_BTN_COLOR)

    def set_theme(self, bg_color: str, txt_color: str, lbl_color: str, btn_color: str):
        self.config(bg=bg_color)
        self.label.config(bg=lbl_color, fg=txt_color)
        self.ok_btn.config(bg=btn_color, fg=txt_color)
        self.cancel_btn.config(bg=btn_color, fg=txt_color)
        self.entry.config(bg=lbl_color, fg=txt_color)


def main():
    game = Wordle("data.db")
    game.run()


if __name__ == "__main__":
    main()
