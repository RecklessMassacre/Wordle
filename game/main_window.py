from typing import Optional, Union
from tkinter import Tk, Label, Frame, Button, PhotoImage, StringVar
from random import sample
from db_handler import DBHandler
from okcancel_window import _OkCancelWindow
from profiles_window import _Profiles
from settings_window import _Settings
from statistics_window import _Statistics


class _Wordle(Tk):
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

        self.protocol("WM_DELETE_WINDOW", self.__on_closing)

    def __ask_load_game(self):
        if self.__autosave:
            if self.db_handler.check_state():
                self.__create_ask_load_window()

    def __create_ask_load_window(self):
        width, length = 300, 100
        oc_window = _OkCancelWindow(width, length, self)
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
        p_window = _Profiles(width, length, self)
        self.center_window(p_window, width, length)

        # lock root window
        p_window.grab_set()

    def __show_settings(self):
        width, length = 400, 300
        set_window = _Settings(width, length, self)
        self.center_window(set_window, width, length)

        # lock root window
        set_window.grab_set()

    def __show_stats(self):
        width, length = 400, 500
        st_window = _Statistics(width, length, self)
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
        """Start mainloop and places everything"""
        self.__place_frames()
        self.__place_labels()
        self.__place_buttons()

        self.__ask_load_game()
        self.mainloop()
