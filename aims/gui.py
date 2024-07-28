import os.path
import json
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import ctypes

import aims.parse
from aims.data_structures import RosterException, InputFileException
from aims.output import csv, ical, efj
from aims.version import VERSION


SETTINGS_FILE = os.path.expanduser("~/.aimsgui")


class ModeSelector(ttk.Frame):

    def __init__(self, parent, with_ade):
        ttk.Frame.__init__(self, parent)
        self.output_type = tk.StringVar()
        self.output_type.set('efj')
        self.with_ade = tk.BooleanVar()
        self.with_ade.set(with_ade)
        self.__make_widgets()

    def __make_widgets(self):
        frm_output_type = ttk.LabelFrame(self, text="Output type")
        frm_output_type.pack(fill=tk.X, expand=True, ipadx=5, pady=5)
        efj_output = ttk.Radiobutton(
            frm_output_type, text=" Flight Journal",
            variable=self.output_type, value='efj',
            command=self.output_type_changed)
        efj_output.pack(fill=tk.X)
        csv_output = ttk.Radiobutton(
            frm_output_type, text=" Logbook (.csv)",
            variable=self.output_type, value='csv',
            command=self.output_type_changed)
        csv_output.pack(fill=tk.X)
        ical_output = ttk.Radiobutton(
            frm_output_type, text=" Roster (.ics)",
            variable=self.output_type, value='ical',
            command=self.output_type_changed)
        ical_output.pack(fill=tk.X)

        self.frm_ical_options = ttk.LabelFrame(self, text="Options")
        with_ade = ttk.Checkbutton(self.frm_ical_options,
                                   text=" All Day Events",
                                   variable=self.with_ade,
                                   command=self.options_changed)
        with_ade.pack(fill=tk.X)

    def output_type_changed(self):
        assert self.output_type.get() in ('csv', 'ical', 'efj')
        if self.output_type.get() == 'ical':
            self.frm_ical_options.pack(fill=tk.X, expand=True, ipadx=5, pady=5)
        else:
            self.frm_ical_options.pack_forget()
        self.event_generate("<<ModeChange>>", when="tail")

    def options_changed(self):
        self.event_generate("<<OptionChange>>", when="tail")


class Actions(ttk.Frame):

    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.__make_widgets()

    def __make_widgets(self):
        frm_1 = ttk.Frame(self)
        frm_1.pack(fill=tk.X)
        btn_convert = ttk.Button(
            frm_1, text="Load Report", width=0,
            command=lambda: self.event_generate("<<Action-Import>>"))
        btn_convert.pack(fill=tk.X)

        frm_2 = ttk.Frame(self)
        frm_2.pack(fill=tk.X, pady=10)
        btn_save = ttk.Button(
            frm_2, text="Save", width=0,
            command=lambda: self.event_generate("<<Action-Save>>"))
        btn_save.pack(fill=tk.X, pady=2)
        self.btn_copy = ttk.Button(
            frm_2, text="Copy All", width=0,
            command=lambda: self.event_generate("<<Action-Copy>>"))
        self.btn_copy.pack(fill=tk.X, pady=2)

        frm_3 = ttk.Frame(self)
        frm_3.pack(fill=tk.X)
        btn_quit = ttk.Button(
            frm_3, text="Quit", width=0,
            command=lambda: self.event_generate("<<Action-Quit>>"))
        btn_quit.pack(fill=tk.X)

    def set_copy_selected(self, selected):
        if selected:
            self.btn_copy.config(text="Copy Selected")
        else:
            self.btn_copy.config(text="Copy All")


class TextWithSyntaxHighlighting(tk.Text):

    def __init__(self, parent=None, **kwargs):
        tk.Text.__init__(self, parent, background='white',
                         wrap="none", **kwargs)
        self.highlight_mode = None
        self.tag_configure("grayed", foreground="#909090")
        self.tag_configure("keyword", foreground="green")
        self.tag_configure("datetime", foreground="blue")
        self.bind(
            '<KeyRelease>',
            lambda *args: self.edit_modified() and self.highlight_syntax())

    def insert(self, idx, text, mode=None, *args):
        tk.Text.insert(self, idx, text, *args)
        if mode:
            self.highlight_mode = mode
            self.highlight_syntax()

    def highlight_syntax(self):
        if not self.highlight_mode:
            return
        for tag in ("keyword", "datetime", "grayed"):
            self.tag_remove(tag, "1.0", "end")
        if self.highlight_mode == 'ical':
            self.highlight_vcalendar()
        elif self.highlight_mode == 'csv':
            self.highlight_csv()
        elif self.highlight_mode == 'efj':
            self.highlight_efj()
        self.edit_modified(False)

    def highlight_vcalendar(self):
        count = tk.IntVar()
        start_idx = "1.0"
        while True:
            new_idx = self.search(
                "(BEGIN|END):VEVENT",
                start_idx, count=count, regexp=True,
                stopindex="end")
            if not new_idx:
                break
            start_idx = f"{new_idx} + {count.get()} chars"
            self.tag_add("keyword", new_idx, start_idx)
        start_idx = "1.0"
        while True:
            new_idx = self.search(
                r"^[\w-]+:",
                start_idx, count=count, regexp=True,
                stopindex="end")
            if not new_idx:
                break
            start_idx = f"{new_idx} + {count.get()} chars"
            self.tag_add("grayed", new_idx, start_idx)
        start_idx = "1.0"
        while True:
            new_idx = self.search(
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}",
                start_idx, count=count, regexp=True,
                stopindex="end")
            if not new_idx:
                break
            start_idx = f"{new_idx} + {count.get()} chars"
            self.tag_add("datetime", new_idx, start_idx)

    def highlight_csv(self):
        count = tk.IntVar()
        start_idx = "1.0"
        while True:
            new_idx = self.search(
                r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}",
                start_idx, count=count, regexp=True,
                stopindex="end")
            if not new_idx:
                break
            start_idx = f"{new_idx} + {count.get()} chars"
            self.tag_add("datetime", new_idx, start_idx)
        start_idx = "1.0"
        while True:
            new_idx = self.search(
                r'(:00)?[",]+',
                start_idx, count=count, regexp=True,
                stopindex="end")
            if not new_idx:
                break
            start_idx = f"{new_idx} + {count.get()} chars"
            self.tag_add("grayed", new_idx, start_idx)

    def highlight_efj(self):
        count = tk.IntVar()
        start_idx = "1.0"
        while True:
            new_idx = self.search(
                r"\d{4}-\d{2}-\d{2}",
                start_idx, count=count, regexp=True,
                stopindex="end")
            if not new_idx:
                break
            start_idx = f"{new_idx} + {count.get()} chars"
            self.tag_add("datetime", new_idx, start_idx)
        start_idx = "1.0"
        while True:
            new_idx = self.search(
                r"\d{4}/\d{4}",
                start_idx, count=count, regexp=True,
                stopindex="end")
            if not new_idx:
                break
            start_idx = f"{new_idx} + {count.get()} chars"
            self.tag_add("datetime", new_idx, start_idx)
        start_idx = "1.0"
        while True:
            new_idx = self.search(
                "CP:|FO:|PU:|FA:",
                start_idx, count=count, regexp=True,
                stopindex="end")
            if not new_idx:
                break
            start_idx = f"{new_idx} + {count.get()} chars"
            self.tag_add("keyword", new_idx, start_idx)


class MainWindow(ttk.Frame):

    def __init__(self, parent):
        ttk.Frame.__init__(self, parent)
        self.parent = parent
        try:
            with open(SETTINGS_FILE) as f:
                self.settings = json.load(f)
        except Exception:
            self.settings = {}
        self.__make_widgets()
        self.txt.insert(tk.END, f"Version: {VERSION}")
        self.copy_mode = "all"

    def __make_widgets(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        sb = ttk.Scrollbar(self, orient='vertical')
        sbx = ttk.Scrollbar(self, orient='horizontal')
        sb.grid(row=0, column=2, sticky=tk.NS)
        sbx.grid(row=1, column=1, sticky=tk.EW)
        sidebar = ttk.Frame(self, width=0)
        sidebar.grid(row=0, column=0, sticky=tk.NS, padx=5, pady=5)
        self.txt = TextWithSyntaxHighlighting(self)
        self.txt.grid(row=0, column=1, sticky=tk.NSEW)
        sb.config(command=self.txt.yview)
        sbx.config(command=self.txt.xview)
        self.txt.config(yscrollcommand=sb.set)
        self.txt.config(xscrollcommand=sbx.set)
        self.txt.bind("<<Selection>>", self.__on_selection_change)

        sidebar.rowconfigure(1, weight=1)
        self.ms = ModeSelector(sidebar,
                               self.settings.get('ADE', True))
        self.ms.bind("<<ModeChange>>", self.__on_mode_change)
        self.ms.bind("<<OptionChange>>", self.__on_option_change)
        self.ms.grid(row=0, sticky=tk.N)
        self.act = Actions(sidebar)
        self.act.grid(row=1, sticky=(tk.EW + tk.S))
        for event, func in (
                ("<<Action-Import>>", self.__import),
                ("<<Action-Copy>>", self.__copy),
                ("<<Action-Save>>", self.__save),
                ("<<Action-Quit>>", lambda _: self.parent.destroy())):
            self.act.bind(event, func)
        self.act.set_copy_selected(False)

    def __on_mode_change(self, _):
        self.txt.delete('1.0', tk.END)

    def __on_option_change(self, _):
        self.settings['ADE'] = self.ms.with_ade.get()
        self.txt.delete('1.0', tk.END)

    def __on_selection_change(self, _):
        if self.txt.tag_ranges("sel"):
            if self.copy_mode == "sel":
                return
            self.copy_mode = "sel"
            self.act.set_copy_selected(True)
        else:
            self.copy_mode = "all"
            self.act.set_copy_selected(False)

    def __import(self, _):
        assert self.ms.output_type.get() in ('csv', 'ical', 'efj')
        try:
            if self.ms.output_type.get() == 'efj':
                self.__efj()
            elif self.ms.output_type.get() == 'csv':
                self.__csv()
            else:
                self.__ical()
        except RosterException as e:
            self.txt.delete('1.0', tk.END)
            messagebox.showerror("Error", str(e))

    def __roster_html(self):
        retval = ""
        path = self.settings.get('openPath')
        fn = filedialog.askopenfilename(
            filetypes=(
                ("HTML file", "*.htm"),
                ("HTML file", "*.html"),
                ("All", "*.*")),
            initialdir=path)
        if fn:
            self.settings['openPath'] = os.path.dirname(fn)
            try:
                with open(fn) as f:
                    retval = f.read()
            except Exception:
                raise InputFileException
        return retval

    def __csv(self):
        txt = ""
        html = self.__roster_html()
        if not html:
            return
        self.txt.delete('1.0', tk.END)
        self.txt.insert(tk.END, "Getting registration and type info...")
        self.txt.update()

        duties, _ = aims.parse.parse(html)
        # note: normalise newlines for Text widget - will restore on output
        txt = csv(duties).replace("\r\n", "\n")
        self.txt.delete('1.0', tk.END)
        self.txt.insert(tk.END, txt, 'csv')

    def __ical(self):
        html = self.__roster_html()
        if not html:
            return
        duties, ade = aims.parse.parse(html)
        # note: normalise newlines for Text widget - will restore on output
        if not self.ms.with_ade.get():
            ade = ()
        txt = ical(duties, ade).replace("\r\n", "\n")
        self.txt.delete('1.0', tk.END)
        self.txt.insert(tk.END, txt, 'ical')

    def __efj(self):
        html = self.__roster_html()
        if not html:
            return
        self.txt.delete('1.0', tk.END)
        self.txt.insert(tk.END, "Working…", 'efj')
        self.txt.update()
        duties, _ = aims.parse.parse(html)
        txt = efj(duties)
        self.txt.delete('1.0', tk.END)
        self.txt.insert(tk.END, txt, 'efj')

    def __copy(self, _):
        self.clipboard_clear()
        if self.copy_mode == "all":
            start, end = '1.0', tk.END
        else:
            start, end = self.txt.tag_ranges("sel")
        text = self.txt.get(start, end)
        # ical and excel dialect csv need DOS style line endings
        if self.ms.output_type in ('ical', 'csv'):
            text = text.replace("\n", "\r\n")
        self.clipboard_append(text)
        messagebox.showinfo('Copy', 'Text copied to clipboard.')

    def __save(self, _):
        output_type = self.ms.output_type.get()
        assert output_type in ('csv', 'ical', 'efj')
        if output_type == 'csv':
            pathtype = 'csvSavePath'
            filetypes = (("CSV file", "*.csv"),
                         ("All", "*.*"))
            default_ext = '.csv'
        elif output_type == 'efj':
            pathtype = 'efjSavePath'
            filetypes = (("Text file", "*.txt"),
                         ("All", "*.*"))
            default_ext = '.txt'
        else:
            pathtype = 'icalSavePath'
            filetypes = (("ICAL file", "*.ics"),
                         ("ICAL file", "*.ical"),
                         ("All", "*.*"))
            default_ext = '.ics'
        path = self.settings.get(pathtype)
        fn = filedialog.asksaveasfilename(
            initialdir=path,
            filetypes=filetypes,
            defaultextension=default_ext)
        if fn:
            self.settings[pathtype] = os.path.dirname(fn)
            with open(fn, "w", encoding="utf-8", newline='') as f:
                text = self.txt.get('1.0', tk.END)
                # ical and excel dialect csv need DOS style line endings
                if output_type in ('ical', 'csv'):
                    text = text.replace("\n", "\r\n")
                f.write(text)
                messagebox.showinfo('Saved', 'Save complete.')

    def destroy(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=4)
        ttk.Frame.destroy(self)


def main():
    if "windll" in dir(ctypes):
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    root = tk.Tk()
    root.title("aimsgui")
    mw = MainWindow(root)
    mw.pack(fill=tk.BOTH, expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
