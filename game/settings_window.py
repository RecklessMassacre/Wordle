from tkinter import Frame, Toplevel, Checkbutton


class _Settings(Toplevel):
    """Settings window"""
    def __init__(self, width: int, length: int, root=None):
        super().__init__(root)
        self.root = root
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
