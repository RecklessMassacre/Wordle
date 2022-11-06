from tkinter import Label, Frame, StringVar, Toplevel, Canvas
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class _Statistics(Toplevel):
    """Statistics window"""
    def __init__(self, width: int, length: int, root=None):
        super().__init__(root)
        self.root = root
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
