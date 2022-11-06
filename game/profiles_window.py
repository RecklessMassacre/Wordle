from tkinter import Label, Frame, Button, Toplevel, Canvas, Scrollbar, Entry
from tkinter.constants import VERTICAL
from tkinter.messagebox import askokcancel, showinfo, WARNING


class _Profiles(Toplevel):
    """Profiles window"""
    def __init__(self, width: int, length: int, root=None):
        super().__init__(root)
        self.root = root
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
        p_window = _ProfileGetterWindow(width, length, self)
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


class _ProfileGetterWindow(Toplevel):
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
