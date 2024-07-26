#https://pythonprogramming.altervista.org/create-more-windows-with-tkinter/?doing_wp_cron=1692785788.4272630214691162109375

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
import os
import manager2

class Window(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.show_widgets()

    def show_widgets(self):
        self.master.title("ImageExtractor")
        self.master.geometry("500x500")
        button1= tk.Button(self, text="Upload directory", command=self.work_with_dir)
        button1.pack(padx=20, pady=30)
        button2 = tk.Button(self, text="Upload link", command=self.work_with_link)
        button2.pack(padx=20, pady=30)
        button3 = tk.Button(self, text="Upload directory with packages", command=self.work_with_batches)
        button3.pack(padx=20, pady=30)
        b_quit = tk.Button(self, text="EXIT", command=self.close_window)
        b_quit.pack(padx=5, pady=100)

    def work_with_batches(self):
        self.dirname = filedialog.askdirectory()
        if self.dirname == "" or self.dirname == " ":
            messagebox.showerror("Error", "Invalid directory name")
        else:
            manager2.work_with_batches(self.dirname)
            self.open_save_win()
        return
    
    def work_with_dir(self):
        language = Language()
        self.continue_with_dir(language.get())

    def continue_with_dir(self, lang):
        self.dirname = filedialog.askdirectory()
        if self.dirname == "" or self.dirname == " ":
            messagebox.showerror("Error", "Invalid directory name")
        else:
            names, metadata = JournalMetadataScrollBar(self.dirname)
            metadata_parsed = self.read_metadata(metadata)
            manager2.work_with_folder(names, metadata_parsed, lang)
            self.open_save_win()

    def read_metadata(self, metadata):
        metadata_read = []
        for i in range(len(metadata)):
            metadata_read.append(metadata[i].get())
        return metadata_read

    def work_with_link(self):
        language = Language()
        self.continue_with_link(language.get())

    def continue_with_link(self, lang):
        link_entry, volume_start, month_start, issue_start = Link()
        v_s = self.convert_str_to_int(volume_start.get())
        m_s = self.convert_str_to_int(month_start.get())
        i_s = self.convert_str_to_int(issue_start.get())
        link = link_entry.get()
        if link == "" or link == " ":
            messagebox.showerror("Error", "Invalid link")
        elif v_s == -1 :
            messagebox.showerror("Error", "Invalid volume start")
        elif m_s == -1:
            messagebox.showerror("Error", "Invalid month start")
        elif i_s == -1:
            messagebox.showerror("Error", "Invalid issue start")
        else:
            manager2.work_with_link(link, lang, v_s, m_s, i_s)
            self.open_save_win()

    def open_save_win(self):
        save_win = tk.Toplevel(self.master)
        save_win.grab_set()
        SaveWindow(save_win)

    def close_window(self):
        self.master.destroy()

    def convert_str_to_int(self, s:str)->int:
        if len(s) == 0: return 0
        if s.isnumeric(): return int(s)-1

        return -1 # error


class SaveWindow(Window):
    def show_widgets(self):
        self.master.title("SaveWindow")
        self.master.geometry("500x500")
        self.l = tk.Label(self.master, text="Files have been processed.\nImages and csv files are in a folder called 'result'.").pack(padx=50, pady=50)
        Button = tk.Button(self.master, text ="SAVE")
        Button.pack(padx=10, pady=10)
        b_quit = tk.Button(self.master, text="EXIT", command=self.close_window)
        b_quit.pack(padx=5, pady=100)



def Language():
    languageWindow = tk.Toplevel()
    languageWindow.title("Language choice")
    languageWindow.geometry("200x200")
    languageWindow.grab_set()

    var = tk.StringVar()
    ces = tk.Radiobutton(languageWindow, text="Czech", variable=var, value='ces')
    ces.pack()
    deu = tk.Radiobutton(languageWindow, text="German", variable=var, value='deu')
    deu.pack()
    fra = tk.Radiobutton(languageWindow, text="French", variable=var, value='fra')
    fra.pack()
    rus = tk.Radiobutton(languageWindow, text="Russian", variable=var, value='rus')
    rus.pack()
    Button = tk.Button(languageWindow, text ="Submit Data", 
                       command = languageWindow.destroy).pack()
    languageWindow.wait_window()
    return var

'''
def JournalMetadata(dir_name):
    metadataWindow = tk.Toplevel()
    metadataWindow.grab_set()
    tk.Label(metadataWindow, text ="Settings Window").grid(row=0)
    count = 0
    metadata = []
    names = []
    entries = os.listdir(dir_name)
    for i, entry in enumerate(entries):
        if is_pdf(entry):
            l = tk.Label(metadataWindow, text=entry).grid(row=i, column=0)
            evar = tk.StringVar()
            note = tk.Entry(metadataWindow, width=30,#30
                            textvariable=evar).grid(row=i,column=1,padx=5,pady=5)
            metadata.append(evar)
            names.append(dir_name+"/"+entry)
            count += 1

    Button = tk.Button(metadataWindow, text ="Submit Data", 
                       command = metadataWindow.destroy).grid(row=count+1)

    metadataWindow.wait_window()
    # print("finished waiting...")
    return (names, metadata)
'''


def JournalMetadataScrollBar(dir_name):
    metadataWindow = tk.Toplevel()
    metadataWindow.geometry("900x500")#500x500
    metadataWindow.grab_set()

    main_frame = tk.Frame(metadataWindow)
    main_frame.pack(fill=tk.BOTH, expand=1)
    my_canvas = tk.Canvas(main_frame)
    my_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
    my_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=my_canvas.yview)
    my_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    my_canvas.configure(yscrollcommand=my_scrollbar)
    my_canvas.bind('<Configure>', lambda e: my_canvas.configure(scrollregion=my_canvas.bbox("all")))
    second_frame = tk.Frame(my_canvas)
    my_canvas.create_window((0,0), window=second_frame, anchor="nw")

    tk.Label(second_frame, text ="Settings Window").grid(row=0)
    count = 0
    metadata = []
    names = []
    entries = os.listdir(dir_name)
    for i, entry in enumerate(entries):
        if is_pdf(entry):
            count += 1
            l = tk.Label(second_frame, text=entry).grid(row=count, column=0)#row=i
            evar = tk.StringVar()
            note = tk.Entry(second_frame, width=80,#30
                            textvariable=evar).grid(row=count,column=1,padx=5,pady=5)#row=i
            metadata.append(evar)
            names.append(dir_name+"/"+entry)
            # count += 1
    # print(count)
    Button = tk.Button(second_frame, text ="Submit Data",
                       command = metadataWindow.destroy).grid(row=count+1)

    metadataWindow.wait_window()
    # print("finished waiting...")
    return (names, metadata)

def Link():
    linkWindow = tk.Toplevel()
    linkWindow.grab_set()
    tk.Label(linkWindow, text ="Enter link").grid(row=0)
    evar = tk.StringVar()
    note = tk.Entry(linkWindow, width=150, 
                    textvariable=evar).grid(row=6,padx=5,pady=5)
    
    tk.Label(linkWindow, text ="Enter volume start").grid(row=7, padx=5,pady=5)
    volume_start = tk.StringVar()
    note1 = tk.Entry(linkWindow, width=20, 
                    textvariable=volume_start).grid(row=8,padx=5,pady=5)
    
    tk.Label(linkWindow, text ="Enter month start (ONLY FOR FRENCH LIBRARY)").grid(row=9, padx=5,pady=5)
    month_start = tk.StringVar()
    note2 = tk.Entry(linkWindow, width=20, 
                    textvariable=month_start).grid(row=10,padx=5,pady=5)
    
    tk.Label(linkWindow, text ="Enter issue start").grid(row=11, padx=5,pady=5)
    issue_start = tk.StringVar()
    note3 = tk.Entry(linkWindow, width=20, 
                    textvariable=issue_start).grid(row=12,padx=5,pady=5)

    Button = tk.Button(linkWindow, text ="OK",
                       command = linkWindow.destroy).grid(row=13)

    linkWindow.wait_window()
    return evar, volume_start, month_start, issue_start

def is_pdf(file_name):
    if file_name.endswith('.pdf'):
        return True
    else:
        return False

def main():
    print (os.getcwd())
    root = tk.Tk()
    Window(root).pack(side="top", fill="both", expand=True)
    root.mainloop()

if __name__ == "__main__":
    main()