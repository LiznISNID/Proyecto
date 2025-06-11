import tkinter as tk
import yaml
from PIL import ImageTk, Image
import os
import time
import cv2
import serial
from datetime import datetime
import csv

class Escanear(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Escanear Rostro")
        self.geometry("800x600")
        try:
            self.config = yaml.safe_load(open("config.yaml"))
        except Exception as e:
            print("Error al cargar el archivo de configuración:", e)
            self.config = {}

        self.original_bg = None
        self.ser = None

        try:
            self.ser = serial.Serial('/dev/ttyUSB1', 9600, timeout=1)
            time.sleep(2)
        except serial.SerialException as e:
            print(f"No se pudo conectar al arduino: {e}")

        self.canvas = tk.Canvas(self, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bind("<Configure>", self.on_resize)
        self.load_background()
        self.show_scan_screen()

    def load_background(self):
        if "main_app" in self.config and "background_image" in self.config["main_app"]:
            try:
                self.original_bg = Image.open(self.config["main_app"]["background_image"])
                self.render_ui()
            except Exception as e:
                print("Error cargando fondo:", e)
                self.original_bg = None
                self.canvas.configure(bg="black")
        else:
            print("No se especificó la ruta de la imagen de fondo en la configuración.")
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

    def show_scan_screen(self):
        self.scan_frame = tk.Frame(self.canvas, bg="", bd=0)
        self.scan_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(self.scan_frame, text="Sistema de Escaneo Facial",
                font=("Arial", 24), fg="white", bg="black").pack(pady=10)

        tk.Label(self.scan_frame, text="Presiona para iniciar el escaneo",
                font=("Arial", 18), fg="white", bg="black").pack(pady=10)

        tk.Button(self.scan_frame, text="Capturar Rostro",
                command=self.reconocimiento_facial,
                bg="#4CAF50", fg="white", font=("Arial", 12),
                width=20).pack(side="left", pady=10)
        
        tk.Button(self.scan_frame, text="Regresar",
                command=self.go_back,
                bg="#F44336", fg="white", font=("Arial", 12),
                width=20).pack(side="left", pady=10)

    def reconocimiento_facial(self):
        dataPath = '/home/Equipo3/Proyecto/Data'
        imagePaths = os.listdir(dataPath)
        print('imagePaths =', imagePaths)

        face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        face_recognizer.read('/home/Equipo3/Proyecto/modeloLBPHFace.xml')

        cap = cv2.VideoCapture('/dev/video0')
        faceClassif = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        start_time = time.time()

        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(script_dir, 'reconocimientos.csv')

        if not os.path.exists(log_path):
            with open(log_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Nombre", "Fecha y Hora"])

        reconocidos = set()
        desconocido_detectado = False

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            auxFrame = gray.copy()

            faces = faceClassif.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                rostro = auxFrame[y:y + h, x:x + w]
                rostro = cv2.resize(rostro, (150, 150), interpolation=cv2.INTER_CUBIC)
                result = face_recognizer.predict(rostro)

                if result[1] < 70:
                    nombre_persona = imagePaths[result[0]]
                    cv2.putText(frame, '{}'.format(nombre_persona), (x, y - 25), 2, 1.1, (0, 255, 0), 1, cv2.LINE_AA)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    if nombre_persona not in reconocidos:
                        self.send_to_arduino('C')
                        now = datetime.now()
                        fecha_hora = now.strftime('%Y-%m-%d %H:%M:%S')
                        with open(log_path, mode='a', newline='') as file:
                            writer = csv.writer(file)
                            writer.writerow([nombre_persona, fecha_hora])
                        reconocidos.add(nombre_persona)

                else:
                    cv2.putText(frame, 'Desconocido', (x, y - 20), 2, 0.8, (0, 0, 255), 1, cv2.LINE_AA)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

                    if not desconocido_detectado:
                        self.send_to_arduino('D')
                        now = datetime.now()
                        fecha_hora = now.strftime('%Y-%m-%d %H:%M:%S')
                        with open(log_path, mode='a', newline='') as file:
                            writer = csv.writer(file)
                            writer.writerow(["Desconocido", fecha_hora])
                        desconocido_detectado = True

            cv2.imshow('frame', frame)

            if time.time() - start_time > 10:
                print("10 segundos transcurridos. Deteniendo el escaneo...")
                break

            if cv2.waitKey(1) == 27:
                break

        cap.release()
        cv2.destroyAllWindows()


    def send_to_arduino(self, value):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(value.encode())
                print(f"Enviado al Arduino: {value}")
            except serial.SerialException as e:
                print(f"Error al enviar dato a Arduino: {e}")

    def go_back(self):
        self.master.deiconify()
        self.destroy()

    def __del__(self):
        if self.ser:
            self.ser.close()
