
import tkinter as tk
from tkinter import ttk,messagebox
from app.services.auth_service import check_login

class App:

    def __init__(self,root):
        self.root=root
        self.login()

    def login(self):
        frame=ttk.Frame(self.root,padding=20)
        frame.pack()

        ttk.Label(frame,text="Usuario").pack()
        self.user=ttk.Entry(frame)
        self.user.pack()

        ttk.Label(frame,text="Senha").pack()
        self.password=ttk.Entry(frame,show="*")
        self.password.pack()

        ttk.Button(frame,text="Entrar",command=self.check).pack()

    def check(self):
        if check_login(self.user.get(),self.password.get()):
            messagebox.showinfo("OK","Login correto")
        else:
            messagebox.showerror("Erro","Login incorreto")

def run_app():
    root=tk.Tk()
    root.title("ERP Paraguay")
    App(root)
    root.mainloop()
