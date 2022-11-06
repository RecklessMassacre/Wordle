from tkinter import Label, Button, Toplevel


class _OkCancelWindow(Toplevel):
    # askokcancel func brings in strange bug
    # of keyboard keybindings stop working for some reason
    # until some action in OS is performed
    def __init__(self, width: int, length: int, root):
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
