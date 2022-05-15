import sqlite3
from typing import Optional, Union
from tkinter import Tk, Label, Frame, Button, PhotoImage, StringVar, Toplevel
from random import sample
from os.path import exists
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
# seems to work correctly without it
# import matplotlib
# matplotlib.use('TkAgg')


class DBHandler:
    # TODO

    def __init__(self, db_file):
        if not exists(db_file):
            raise sqlite3.Error("db doesn't exist")

        self._conn = sqlite3.connect(db_file)
        self._cur = self._conn.cursor()

    def get_words(self):
        sql = "SELECT * FROM words"
        self._cur.execute(sql)

        arr = [item[0] for item in self._cur.fetchall()]
        return arr

    def close(self):
        self._conn.close()


class Wordle:
    def __init__(self, filename: str, db_name: str):
        # sqlite3
        self.db_handler: DBHandler = DBHandler(db_name)

        # root initialization
        self.window_width: int = 820
        self.window_length: int = 820
        self.root: Tk = Tk()

        # game data
        self.ROW_AMOUNT: int = 6
        self.row_length: int = 5
        self.filename: str = filename
        self.words_list: Optional[list[str]] = self.db_handler.get_words()  # all 5-letters words
        self.chosen_word: str = sample(self.words_list, 1)[0].upper()  # word to guess
        self.input_word: list[str] = [str() for _ in range(self.row_length)]
        self.cur_row: int = 1
        self.label_pointer: int = 0
        self.game_flag: bool = True
        # each number is alphabet position and each array position is keyboard position
        self.numerical_keyboard = [
            10, 23, 20, 11, 5, 14, 3, 25, 26, 8, 22, 27,
            21, 28, 2, 0, 16, 17, 15, 12, 4, 7, 30, 6,
            32, 24, 18, 13, 9, 19, 29, 1, 31
        ]

        # zero size image, used to make labels quadratic
        self.image: PhotoImage = PhotoImage()

        # frames definition
        # self.main_frame: Frame = Frame(self.root)
        self.gfield_frame: Frame = Frame(self.root)
        self.menu_frame_left: Frame = Frame(self.root)
        self.menu_frame_right: Frame = Frame(self.root)
        self.keyboard_frame: Frame = Frame(self.root)
        self.messages_frame: Frame = Frame(self.root)

        # labels and its requirements definition and initialization
        # message label
        self.message_label: Optional[Label] = None
        self.message_label_var: StringVar = StringVar()
        self.message_label_var.set('Привет!\nДля ввода букв с клавиатуры нужно перевести раскладку на англ.')

        # game field labels
        self.labels_dict: dict[str, Label] = {}
        self.text_vars: list[StringVar] = [StringVar() for _ in range(self.row_length * self.ROW_AMOUNT)]
        self.init_labels()

        # buttons and its requirements definition and initialization
        self.BASE_COLOR: str = '#f0f0f0'
        self.alphabet: list[str] = [chr(i) for i in range(ord('а'), ord('а') + 6)] + \
                                   [chr(ord('а') + 33)] + \
                                   [chr(i) for i in range(ord('а') + 6, ord('а') + 32)]
        self.state_to_color_dict: dict[int, str] = {1: 'grey', 2: 'yellow', 3: 'green'}  # state: color
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
        self.debug: Optional[Button] = None

        self.init_buttons()

        # root setup
        self.root_setup()

        # placing everything
        self.place_frames()
        self.place_labels()
        self.place_buttons()

    @staticmethod
    def center_window(window, w_width, w_length):
        x = window.winfo_screenwidth() // 2 - w_width // 2
        y = window.winfo_screenheight() // 2 - w_length // 2
        window.geometry(f"{w_width}x{w_length}+{x}+{y}")

    def root_setup(self):
        self.root.title("Wordle")
        self.center_window(self.root, self.window_width, self.window_length)
        self.root.minsize(width=self.window_width, height=self.window_length)

        # lets root to fill all remaining space, so main frame will always be centered
        self.root.grid_columnconfigure(0, weight=1)

        # Allowing typing letters from keyboard
        eng_keyboard = list("qwertyuiop[]asdfghjkl;'`zxcvbnm,.")
        for i in range(33):
            self.root.bind(
                eng_keyboard[i],
                lambda event, ru_letter=self.alphabet[self.numerical_keyboard[i]].upper(): self.button_click(ru_letter)
            )
        # for Caps Lock
        for i in range(33):
            self.root.bind(
                eng_keyboard[i].upper(),
                lambda event, ru_letter=self.alphabet[self.numerical_keyboard[i]].upper(): self.button_click(ru_letter)
            )

        self.root.bind("<BackSpace>", lambda event: self.clear())
        self.root.bind("<Return>", lambda event: self.enter())

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
                self.keyboard_frame, text=letter,
                command=lambda a=letter: self.button_click(a)  # !!!
            )

        self.clear_button = Button(self.keyboard_frame, text="Очистить", command=self.clear)
        self.enter_button = Button(self.keyboard_frame, text="Ввод ", command=self.enter)

        # Debug button
        self.debug = Button(self.menu_frame_left, height=1, width=5, text="asdas", command=self.debug_a)

        # menu frame
        self.ng_button = Button(self.menu_frame_left, height=1, width=5, text="Заново", command=self.new_game)
        self.stat_button = Button(self.menu_frame_right, height=1, width=5, text="Статистика", command=self.show_stats)
        self.settings_button = Button(self.menu_frame_right, height=1, width=5, text="Параметры", command=self.settings)

    def debug_a(self):
        colors = {}
        for i in range(self.ROW_AMOUNT):
            for j in range(self.row_length):
                colors[f'lbl{i}{j}'] = self.labels_dict[f'lbl{i}{j}'].cget("bg")

        print("lbl states: ", colors)
        print("btn states: ", self.buttons_states)

    def settings(self):
        pass

    def show_stats(self):
        width, length = 400, 500
        st_window = Statistics(width, length, self.root)
        self.center_window(st_window, width, length)

        # lock root window
        st_window.grab_set()

    def place_frames(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=5)

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
        self.debug.grid(ipadx=20, ipady=5, column=1, row=0)

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
        # terrible alg, but working one...
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
            self.labels_dict[f"lbl{i}{j}"].configure(background=color)

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
        self.root.mainloop()

    def congratulate(self):
        self.message_label_var.set(f'Поздраляю! Загадано было слово: {self.chosen_word}\nДля начала новой игры '
                                   f'нажмите кнопку "заново".')
        self.game_flag = False

    def re_init_labels(self):
        for item in self.text_vars:
            item.set('')

        for item in self.labels_dict.values():
            item.configure(background='white')

        self.message_label_var.set('')

    def re_init_buttons(self):
        for item in self.btn_dict.values():
            item.configure(bg=self.BASE_COLOR)

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
    def __init__(self, width, length, root=None):
        super().__init__(root)
        self.title("Statistics")
        self.grid_columnconfigure(0, weight=1)
        self.minsize(width=width, height=length)
        self.resizable(False, False)
        self.BASE_COLOR: str = '#f0f0f0'

        # frames
        self.upper_frame = Frame(self)
        self.lower_frame = Frame(self)

        # upper frame labels and vars
        self.upper_head_lbl = Label(self.upper_frame, text="СТАТИСТИКА", font=("Arial bold", 18))

        # 0 - 2 columns
        self.g_played_number_var = StringVar()
        self.g_played_number_var.set('0')
        self.g_played_number_lbl = Label(
            self.upper_frame, font=("Arial bold", 18), textvariable=self.g_played_number_var
        )
        self.g_played_text_lbl = Label(self.upper_frame, text="Сыграно")

        # 3 - 5 columns
        self.winrate_number_var = StringVar()
        self.winrate_number_var.set('0')
        self.winrate_number_lbl = Label(
            self.upper_frame, font=("Arial bold", 18), textvariable=self.winrate_number_var
        )
        self.winrate_text_lbl = Label(self.upper_frame, text="% побед")

        # 6 - 8 columns
        self.cur_streak_number_var = StringVar()
        self.cur_streak_number_var.set('0')
        self.cur_streak_number_lbl = Label(
            self.upper_frame, font=("Arial bold", 18), textvariable=self.cur_streak_number_var
        )
        self.cur_streak_text_lbl = Label(self.upper_frame, text="Тек. серия\nпобед")

        # 9 - 11 columns
        self.max_streak_number_var = StringVar()
        self.max_streak_number_var.set('0')
        self.max_streak_number_lbl = Label(
            self.upper_frame, font=("Arial bold", 18), textvariable=self.max_streak_number_var
        )
        self.max_streak_text_lbl = Label(self.upper_frame, text="Макс.серия\nпобед")

        # lower frame labels and vars
        self.lower_head_lbl = Label(self.lower_frame, text="РАСПРЕДЕЛЕНИЕ ПОПЫТОК", font=("Arial bold", 18))
        self.barchart_canvas = self.make_barchart()

        self.place_upper_frame_and_labels()
        self.place_lower_frame_and_labels()

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

    def make_barchart(self):
        # the Figure class represents the drawing area on which matplotlib charts will be drawn
        figure = Figure(figsize=(2.5, 2.5), dpi=100)
        figure.patch.set_facecolor(self.BASE_COLOR)

        # the FigureCanvasTkAgg connects the Figure object with a Tkinter’s Canvas object
        figure_canvas = FigureCanvasTkAgg(figure, self.lower_frame)

        # adding a subplot to the figure and returning the axes of the subplot
        axes = figure.add_subplot()

        # get data for barchart
        # TODO
        attempts = [i for i in range(1, 7)]
        scores = [2, 3, 4, 1, 5, 6]

        bars = axes.barh(attempts, scores)

        axes.set_facecolor(self.BASE_COLOR)

        # remove x axis
        axes.get_xaxis().set_visible(False)

        # remove borders
        axes.spines['top'].set_visible(False)
        axes.spines['bottom'].set_visible(False)
        axes.spines['right'].set_visible(False)
        axes.spines['left'].set_visible(False)

        axes.set_yticks(attempts)

        # put values on the right of the bars
        axes.bar_label(bars)

        return figure_canvas.get_tk_widget()


def main():
    game = Wordle("words_wordle.txt", "data.db")
    game.run()

    # closing connection to db explicitly just in case
    game.db_handler.close()


if __name__ == "__main__":
    main()
