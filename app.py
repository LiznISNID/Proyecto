import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image
import yaml
import os
import webbrowser
import csv
from modules.agregar_usuario import AgregarUsuario
from modules.escanear import Escanear

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config = yaml.safe_load(open("config.yaml"))
        self.title(self.config["main_app"]["title"])
        self.geometry(f"{self.config['main_app']['width']}x{self.config['main_app']['height']}")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')  

        self.alpha = 0
        self.slogan_text = "Tu rostro es la llave.\nNuestra tecnología, la puerta."
        
        self.setup_ui()
        self.animate_slogan()

    def setup_ui(self):
        self.canvas = tk.Canvas(self, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.load_images()
        self.create_buttons()
        self.bind("<Configure>", self.on_window_resize)

    def create_buttons(self):
        button_frame = tk.Frame(self.canvas, bg="")
        button_frame.place(relx=0.5, rely=0.75, anchor="center")

        buttons = [
            {"text": "Agregar Usuario", "bg": "#C71585", "active": "#EE5253", "cmd": self.open_agregar_usuario},
            {"text": "Escanear", "bg": "#002147", "active": "#0ABDE3", "cmd": self.open_escanear},
            {"text": "Registro", "bg": "#8A2BE2", "active": "#38A3A5", "cmd": self.open_registro}
        ]

        for btn_config in buttons:
            style_name = f"{btn_config['bg']}.TButton"
            self.style.configure(style_name,
                foreground="white",
                background=btn_config["bg"],
                font=('Arial', 12, 'bold'),
                width=15,
                borderwidth=0,
                focuscolor=btn_config["bg"]
            )
            self.style.map(style_name,
                background=[('active', btn_config["active"])]
            )
            
            btn = ttk.Button(
                button_frame,
                text=btn_config["text"],
                style=style_name,
                command=btn_config["cmd"]
            )
            btn.pack(pady=8, ipadx=5, ipady=3)

    def load_images(self):
        try:
            self.original_bg = Image.open(self.config["main_app"]["background_image"])
            self.original_logo = Image.open("assets/logo.png")
            self.render_ui()
        except Exception as e:
            print("Error cargando imágenes:", e)
            error_label = tk.Label(self, text="Error cargando recursos", 
                                 bg="white", fg="red", font=('Arial', 14))
            error_label.place(relx=0.5, rely=0.5, anchor="center")

    def render_ui(self):
        win_width = self.winfo_width()
        win_height = self.winfo_height()
        
        if win_width < 10 or win_height < 10:
            return
            
        self.canvas.delete("all")
        
        bg_ratio = self.original_bg.width / self.original_bg.height
        win_ratio = win_width / win_height
        
        if win_ratio > bg_ratio:
            new_height = win_height
            new_width = int(new_height * bg_ratio)
        else:
            new_width = win_width
            new_height = int(new_width / bg_ratio)
        
        resized_bg = self.original_bg.resize((new_width, new_height))
        self.bg_image = ImageTk.PhotoImage(resized_bg)
        self.canvas.create_image(win_width//2, win_height//2, 
                                 image=self.bg_image, anchor="center")
        
        logo_size = min(win_width, win_height) // 5
        resized_logo = self.original_logo.resize((logo_size, logo_size))
        self.logo_image = ImageTk.PhotoImage(resized_logo)
        self.canvas.create_image(win_width//2, win_height//4, 
                                 image=self.logo_image, anchor="center")
        
        gray_value = min(255, int(255 * self.alpha))
        text_color = f"#{gray_value:02x}{gray_value:02x}{gray_value:02x}"
        
        self.canvas.create_text(
            win_width//2,
            win_height//4 + logo_size//2 + 35,
            text=self.slogan_text,
            font=("Arial", max(14, int(win_width/50)), "bold"),
            fill=text_color,
            justify="center",
            width=win_width*0.7,
            tags="slogan"
        )

    def open_agregar_usuario(self):
        self.withdraw()
        AgregarUsuario(self)

    def open_escanear(self):
        self.withdraw()
        Escanear(self)

    def open_registro(self):
        webbrowser.open("http://localhost:9090")

    def on_window_resize(self, event=None):
        if event and event.widget == self:
            self.render_ui()

    def animate_slogan(self):
        if self.alpha < 1:
            self.alpha += 0.02
            self.render_ui()
            self.after(100, self.animate_slogan)
        else:
            self.canvas.itemconfig("slogan", fill="white")

if __name__ == "__main__":
    app = App()
    app.mainloop()
