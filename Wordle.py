# from tkinter import *
from typing import Optional, Union
from tkinter import Tk, Label, Frame, Button, PhotoImage, StringVar
from random import sample


class Wordle:
    def __init__(self, filename: str):
        # Root setup
        self.window_width: int = 820
        self.window_length: int = 800
        self.root: Tk = Tk()
        self.root.title("Wordle")
        self.root.geometry(f"{self.window_width}x{self.window_length}")

        # lets root to fill all remaining space, so main frame will always be centered
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Game data
        # loading words
        self.ROW_LENGTH: int = 5
        self.ROW_AMOUNT: int = 6
        self.filename: str = filename
        self.words_list: Optional[list[str]] = self.load_txt(self.filename)  # all 5-letters words
        self.chosen_word: str = sample(self.words_list, 1)[0].upper()  # word to guess

        self.input_word: list[str] = [str() for _ in range(self.ROW_LENGTH)]
        self.cur_row: int = 1
        self.label_pointer: int = 0
        self.game_flag: bool = True

        # Frames definition
        self.main_frame: Frame = Frame(self.root)
        self.gfield_frame: Frame = Frame(self.main_frame)
        self.menu_frame: Frame = Frame(self.main_frame)
        self.keyboard_frame: Frame = Frame(self.main_frame)
        self.messages_frame: Frame = Frame(self.main_frame)

        # Labels and its requirements definition and initialization
        self.message_label: Optional[Label] = None
        self.message_label_var: StringVar = StringVar()
        self.message_label_var.set('Привет!')
        self.labels_dict: dict[str, Label] = {}
        self.text_vars: list[StringVar] = [StringVar() for _ in range(self.ROW_LENGTH * self.ROW_AMOUNT)]
        self.init_labels()

        # Buttons and its requirements definition and initialization
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
        self.init_buttons()

        # Placing everything
        self.place_frames()
        self.place_labels()
        self.place_buttons()

    @staticmethod
    def load_txt(filename):
        with open(filename, 'r') as f:
            arr = f.readlines()
        arr = [item[:-1] for item in arr]
        return arr

    def init_labels(self):
        for i in range(self.ROW_AMOUNT):
            for j in range(self.ROW_LENGTH):
                self.labels_dict[f'lbl{i}{j}'] = Label(
                    self.gfield_frame, font=('Arial bold', 20), background='white',
                    width=60, height=60, image=PhotoImage(), compound='center',
                    textvariable=self.text_vars[self.ROW_LENGTH * i + j]
                )

        self.message_label = Label(
            self.messages_frame, width=100, height=2, textvariable=self.message_label_var,
            font=('Arial', 10)
        )

    def init_buttons(self):
        for i in range(33):
            letter = self.alphabet[i].upper()

            self.btn_dict[f'btn{i}'] = Button(
                self.keyboard_frame, text=letter,
                command=lambda a=letter: self.button_click(a)  # !!!
            )

        self.clear_button = Button(self.keyboard_frame, text="Очистить", command=self.clear)
        self.enter_button = Button(self.keyboard_frame, text="Ввод ", command=self.enter)
        self.ng_button = Button(self.menu_frame, text="Заново", command=self.new_game)

    def place_frames(self):
        self.main_frame.grid(sticky="NS")
        self.menu_frame.grid(sticky="NS")
        self.gfield_frame.grid(sticky="NS")
        self.messages_frame.grid(sticky="NS")
        self.keyboard_frame.grid(sticky="NS")

    def place_labels(self):
        for i in range(self.ROW_AMOUNT):
            for j in range(self.ROW_LENGTH):
                self.labels_dict[f'lbl{i}{j}'].grid(column=j, row=i, padx=10, pady=10)

        self.message_label.grid()

    def place_buttons(self):
        # each number is alphabet position and each array position is keyboard position
        numerical_keyboard = [
            10, 23, 20, 11, 5, 14, 3, 25, 26, 8, 22, 27,
            21, 28, 2, 0, 16, 17, 15, 12, 4, 7, 30, 6,
            32, 24, 18, 13, 9, 19, 29, 1, 31
        ]
        # keyboard frame
        # one button = 2 colons as default
        for i in range(0, 48, 2):
            self.btn_dict[f'btn{numerical_keyboard[i // 2]}'].grid(
                padx=10, pady=10, ipadx=10, ipady=10, column=i % 24, row=i // 24, columnspan=2
            )
        self.enter_button.grid(padx=10, pady=10, ipadx=10, ipady=10, column=0, row=2, columnspan=3, sticky='W')
        for i in range(50, 68, 2):
            self.btn_dict[f'btn{numerical_keyboard[i // 2 - 1]}'].grid(
                padx=10, pady=10, ipadx=10, ipady=10, column=i % 24 + 1, row=i // 24, columnspan=2
            )
        self.clear_button.grid(padx=10, pady=10, ipadx=10, ipady=10, column=21, row=2, columnspan=3, sticky='E')

        # menu frame
        self.ng_button.grid(ipadx=50, ipady=5)

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
        # terrible alg, but working one, i guess...
        s = [1 for _ in range(len(a))]
        a_dict = self._to_dict(a)
        b_dict = self._to_dict(b)
        # print(f'a: {a_dict}\nb: {b_dict}')
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

        # print(f'a: {a_dict}\nb: {b_dict}')
        return s

    def paint_row(self, states: list):
        i = self.label_pointer // self.ROW_LENGTH - 1
        for j in range(len(states)):
            state = states[j]
            color = self.state_to_color_dict[state]
            self.labels_dict[f'lbl{i}{j}'].configure(
                background=color, image=PhotoImage(), compound='center'
            )

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

        if self.label_pointer % self.ROW_LENGTH == 0 and self.cur_row == self.label_pointer // self.ROW_LENGTH:
            return True
        return False

    def check_word_in_dict(self):
        word = ''.join(self.input_word).lower()
        if word in self.words_list:
            return True
        return False

    def get_input_word(self):
        for i in range((self.cur_row - 1) * self.ROW_LENGTH, self.cur_row * self.ROW_LENGTH):
            self.input_word[i % self.ROW_LENGTH] = self.text_vars[i].get()

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
            if (self.cur_row - 1) * self.ROW_LENGTH < self.label_pointer <= self.cur_row * self.ROW_LENGTH:
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
            item.configure(
                background='white', image=PhotoImage(), compound='center'
            )

        self.message_label_var.set('')

    def re_init_buttons(self):
        for item in self.btn_dict.values():
            item.configure(bg='#f0f0f0')

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


def main():
    game = Wordle('words_wordle.txt')
    game.run()


if __name__ == '__main__':
    main()
