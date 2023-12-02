import tkinter as tk
from tkinter import ttk
import ctypes

from client import conf, crypt_available
from host_main import start as h_start
from guest_main import start as v_start
from gui_component import *

HOST = "host"
GUEST = "guest"
OPTION = "option"


class MainWindow(tk.Tk):

    def __init__(self, title, size):
        super().__init__()

        self.title(title)
        self.geometry(size)

        self.__task_manager = TaskManager(times=1, mutex=False)
        self.__notebook = ttk.Notebook(self, width=20, height=20)
        self.__msg_pipe = {
            HOST: MessagePipe(),
            GUEST: MessagePipe(),
        }
        self.__frame = {
            HOST: ClientFrame(self.__task_manager, h_start, HOST, conf,
                              self.__msg_pipe[HOST], borderwidth=0),
            GUEST: ClientFrame(self.__task_manager, v_start, GUEST, conf,
                               self.__msg_pipe[GUEST], borderwidth=0),
            OPTION: OptionFrame(self.__task_manager, conf, crypt_available,
                                self.__msg_pipe, borderwidth=1),
        }

        self.__notebook.add(self.__frame[HOST], text=HOST)
        self.__notebook.add(self.__frame[GUEST], text=GUEST)
        self.__notebook.add(self.__frame[OPTION], text=OPTION)
        self.__notebook.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        ctypes.windll.shcore.SetProcessDpiAwareness(1)


if __name__ == "__main__":
    root = MainWindow("client_v2.0.0", "750x500")
    root.mainloop()
