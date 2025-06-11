import tkinter as tk
from tkinter import messagebox
from PIL import ImageTk, Image
import yaml
import os
import serial
import cv2
import imutils
import numpy as np

class AgregarUsuario(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Agregar Usuario")
        self.geometry("800x600")
        self.minsize(600, 400)
        self.master = master
        self.master_password = "admin123"
        self.rfid_autorizado = "4F0088B20772"

        self.config = yaml.safe_load(open("config.yaml"))

        self.authenticated = False
        self.original_bg = None
        self.bg_image = None
        self.ser = None

        try:
            self.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
        except serial.SerialException as e:
            print(f"No se pudo conectar al lector RFID: {e}")

        self.canvas = tk.Canvas(self, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bind("<Configure>", self.on_resize)

        self.setup_ui()
        self.load_background()

    def load_background(self):
        try:
            self.original_bg = Image.open(self.config["main_app"]["background_image"])
            self.render_ui()
        except Exception as e:
            print("Error cargando fondo:", e)
            self.canvas.configure(bg="black")

    def on_resize(self, event):
        if self.original_bg:
            self.render_ui()

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
        self.canvas.create_image(win_width // 2, win_height // 2, image=self.bg_image, anchor="center")

    def setup_ui(self):
        if not self.authenticated:
            self.show_auth_screen()
        else:
            self.show_user_form()

    def show_auth_screen(self):
        self.auth_frame = tk.Frame(self.canvas, bg="", bd=0)
        self.auth_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(self.auth_frame, text="Autenticación Requerida",
                font=("Arial", 24), fg="white", bg="black").pack(pady=10)

        tk.Label(self.auth_frame, text="Contraseña Maestra:",
                font=("Arial", 16), fg="white", bg="black").pack()

        self.password_entry = tk.Entry(self.auth_frame, show="*", font=("Arial", 12), width=20)
        self.password_entry.pack(pady=5)

        tk.Button(self.auth_frame, text="Verificar Contraseña",
                command=self.verify_password,
                bg="#4CAF50", fg="white", font=("Arial", 12),
                width=20).pack(pady=10)

        tk.Label(self.auth_frame, text="Usar tarjeta autorizada",
                font=("Arial", 14), fg="white", bg="black").pack(pady=5)

        tk.Button(self.auth_frame, text="Regresar",
                command=self.go_back,
                bg="#F44336", fg="white", font=("Arial", 12),
                width=20).pack(pady=10)
        
        self.status_label = tk.Label(self.auth_frame, text="", font=("Arial", 10), fg="white", bg="black")
        self.status_label.pack(pady=5)

        if self.ser:
            self.after(100, self.verificar_rfid)

    def verificar_rfid(self):
        try:
            if self.ser and self.ser.in_waiting > 0:
                raw_bytes = self.ser.readline()
                raw_data = raw_bytes.decode('utf-8', errors='ignore').strip()

                uid_clean = raw_data.upper().replace('\r', '').replace('\n', '').replace(' ', '')
                uid_clean = uid_clean.replace('\x02', '').replace('\x03', '') 
                uid_clean = ''.join(char for char in uid_clean if ord(char) > 31)

                if not uid_clean or len(uid_clean) < 6:
                    return 

                if not hasattr(self, 'ultimo_uid'):
                    self.ultimo_uid = None

                if uid_clean == self.ultimo_uid:
                    return

                self.ultimo_uid = uid_clean 
                if uid_clean == self.rfid_autorizado:
                    self.authenticated = True
                    self.auth_frame.destroy()
                    if self.ser.is_open:
                        self.ser.close()
                    self.render_ui()
                    self.show_user_form()
                    return
                else:
                    self.status_label.config(text="Tarjeta no autorizada", fg="red")
                    self.after(3000, lambda: self.status_label.config(text=""))
                    self.after(100, self.verificar_rfid)

        except Exception as e:
            print("Error leyendo del lector RFID:", e)

        self.after(100, self.verificar_rfid)


    def verify_password(self):
        if self.password_entry.get() == self.master_password:
            self.authenticated = True
            self.auth_frame.destroy()
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.render_ui()
            self.show_user_form()
        else:
            messagebox.showerror("Error", "Contraseña incorrecta")
            self.password_entry.delete(0, tk.END)

    def show_user_form(self):
        self.form_frame = tk.Frame(self.canvas, bg="", bd=0)
        self.form_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(self.form_frame, text="Agregar Nuevo Usuario",
                 font=("Arial", 24), fg="white", bg="black").pack(pady=10)

        fields = [("Nombre:", "nombre"), ("ID:", "id"), ("Contraseña:", "password")]
        self.entries = {}

        for label_text, field_name in fields:
            tk.Label(self.form_frame, text=label_text,
                     font=("Arial", 16), fg="white", bg="black").pack()

            entry = tk.Entry(self.form_frame,
                             font=("Arial", 12),
                             width=25,
                             show="*" if "password" in field_name else None)
            entry.pack(pady=5)
            self.entries[field_name] = entry

        tk.Button(self.form_frame, text="Guardar",
                  command=self.save_user,
                  bg="#2196F3", fg="white", font=("Arial", 12),
                  width=15).pack(pady=10)

        tk.Button(self.form_frame, text="Regresar",
                  command=self.go_back,
                  bg="#F44336", fg="white", font=("Arial", 12),
                  width=15).pack()

    def save_user(self):
        user_data = {
            "nombre": self.entries["nombre"].get(),
            "id": self.entries["id"].get(),
            "password": self.entries["password"].get()
        }

        if not all(user_data.values()):
            messagebox.showwarning("Advertencia", "Todos los campos son obligatorios")
            return

        base_path = '/home/Equipo3/Proyecto/Data'
        folder_name = user_data["nombre"].strip().replace(" ", "_")
        user_folder_path = os.path.join(base_path, folder_name)

        try:
            os.makedirs(user_folder_path, exist_ok=True)
            print(f"Carpeta creada: {user_folder_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la carpeta: {e}")
            return

        messagebox.showinfo("Éxito", f"Usuario agregado correctamente.\nCarpeta creada en:\n{user_folder_path}")
        self.clear_form()
        self.capturar_rostros(user_data["nombre"], base_path)
        self.entrenar_modelo()

    def clear_form(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)

    def capturar_rostros(self, nombre, ruta):
        personPath = os.path.join(ruta, nombre.replace(" ", "_"))
        if not os.path.exists(personPath):
            os.makedirs(personPath)

        cap = cv2.VideoCapture('/dev/video0')
        faceClassif = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        count = 0

        while True:
            ret, frame = cap.read()
            if ret == False: break
            frame = imutils.resize(frame, width=640)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            auxFrame = frame.copy()

            faces = faceClassif.detectMultiScale(gray, 1.3, 5)

            for (x,y,w,h) in faces:
                cv2.rectangle(frame, (x,y),(x+w,y+h),(0,255,0),2)
                rostro = auxFrame[y:y+h,x:x+w]
                rostro = cv2.resize(rostro,(150,150),interpolation=cv2.INTER_CUBIC)
                cv2.imwrite(personPath + '/rostro_{}.jpg'.format(count),rostro)
                count = count + 1
            cv2.imshow('frame',frame)

            k = cv2.waitKey(1)
            if k == 27 or count >= 500:
                break

        cap.release()
        cv2.destroyAllWindows()

    def entrenar_modelo(self):
        dataPath = '/home/Equipo3/Proyecto/Data'
        peopleList = os.listdir(dataPath)
        print('Lista de personas: ', peopleList)

        labels = []
        facesData = []
        label = 0

        for nameDir in peopleList:
            personPath = os.path.join(dataPath, nameDir)
            print('Leyendo las imágenes')

            for fileName in os.listdir(personPath):
                print('Rostros: ', nameDir + '/' + fileName)
                labels.append(label)
                facesData.append(cv2.imread(os.path.join(personPath, fileName), 0))
            label = label + 1

        face_recognizer = cv2.face.LBPHFaceRecognizer_create()

        print("Entrenando...")
        face_recognizer.train(facesData, np.array(labels))

        modelo_path = '/home/Equipo3/Proyecto/modeloLBPHFace.xml'
        face_recognizer.write(modelo_path)
        print(f"Modelo almacenado en {modelo_path}...")

    def go_back(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.master.deiconify()
        self.destroy()
