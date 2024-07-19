import cv2
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image
import time
import ctypes
import os
import tempfile
import threading
import json
import shutil
import webbrowser

class ClockOverlay:
    def __init__(self, notebook):
        self.clock_tab = ttk.Frame(notebook)
        notebook.add(self.clock_tab, text="Relógio")
        
        self.clock_window = tk.Toplevel()
        self.clock_window.attributes('-topmost', True)
        self.clock_window.overrideredirect(True)
        self.clock_window.geometry("+0+0")
        
        self.time_label = tk.Label(self.clock_window, font=('Helvetica', 16), fg='white', bg='black')
        self.time_label.pack()

        self.show_seconds = tk.BooleanVar(value=True)
        self.show_date = tk.BooleanVar(value=True)
        self.update_clock()

        self.seconds_check = tk.Checkbutton(self.clock_tab, text="Mostrar Segundos", variable=self.show_seconds)
        self.seconds_check.pack()

        self.date_check = tk.Checkbutton(self.clock_tab, text="Mostrar Data", variable=self.show_date)
        self.date_check.pack()

        self.color_button = tk.Button(self.clock_tab, text="Alterar Cor do Texto", command=self.change_text_color)
        self.color_button.pack()

        self.bg_color_button = tk.Button(self.clock_tab, text="Alterar Cor do Fundo", command=self.change_bg_color)
        self.bg_color_button.pack()

        self.toggle_clock_button = tk.Button(self.clock_tab, text="Exibir/Ocultar Relógio", command=self.toggle_clock)
        self.toggle_clock_button.pack()

        self.clock_window.withdraw()  # Oculta o relógio ao iniciar

    def update_clock(self):
        now = time.strftime("%H:%M:%S" if self.show_seconds.get() else "%H:%M")
        if self.show_date.get():
            now = time.strftime("%Y-%m-%d ") + now
        self.time_label.config(text=now)
        self.clock_window.after(1000, self.update_clock)

    def change_text_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.time_label.config(fg=color)

    def change_bg_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.clock_window.config(bg=color)
            self.time_label.config(bg=color)

    def toggle_clock(self):
        if self.clock_window.winfo_viewable():
            self.clock_window.withdraw()
        else:
            self.clock_window.deiconify()

class VideoPlayer:
    def __init__(self, notebook):
        self.video_tab = ttk.Frame(notebook)
        notebook.add(self.video_tab, text="Vídeo")
        
        self.label = tk.Label(self.video_tab)
        self.label.pack()
        
        self.btn_select_video = tk.Button(self.video_tab, text="Selecionar Vídeo", command=self.select_video)
        self.btn_select_video.pack()

        self.btn_select_image = tk.Button(self.video_tab, text="Selecionar Imagem Padrão ao fechar", command=self.select_image)
        self.btn_select_image.pack()

        self.speed_label = tk.Label(self.video_tab, text="Ajuste a velocidade de exibição (valores menores = mais rápido, valores maiores = mais lento):")
        self.speed_label.pack()

        self.speed_var = tk.DoubleVar(value=1/24)
        self.spinbox = tk.Spinbox(self.video_tab, from_=0.01, to=1.0, increment=0.01, textvariable=self.speed_var, format="%.2f")
        self.spinbox.pack()

        self.status_label = tk.Label(self.video_tab, text="Status: Não exibindo nada")
        self.status_label.pack()

        self.prev_videos_listbox = tk.Listbox(self.video_tab)
        self.prev_videos_listbox.pack()
        self.prev_videos_listbox.bind('<<ListboxSelect>>', self.on_video_select)

        self.load_previous_videos()

    def load_previous_videos(self):
        try:
            with open("video_info.json", "r") as f:
                self.prev_videos = json.load(f).get("video_paths", [])
                for video in self.prev_videos:
                    self.prev_videos_listbox.insert(tk.END, video)
        except (FileNotFoundError, json.JSONDecodeError):
            self.prev_videos = []

    def select_video(self):
        video_path = filedialog.askopenfilename(title="Selecionar Vídeo", filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")])
        if not video_path:
            messagebox.showwarning("Aviso", "Nenhum vídeo selecionado.")
            return
        self.prev_videos.append(video_path)
        self.prev_videos_listbox.insert(tk.END, video_path)
        self.save_video_info()

    def select_image(self):
        image_path = filedialog.askopenfilename(title="Selecionar Imagem", filetypes=[("Image files", "*.jpg;*.jpeg;*.png"), ("All files", "*.*")])
        if not image_path:
            messagebox.showwarning("Aviso", "Nenhuma imagem selecionada.")
            return
        self.set_wallpaper_image(image_path)

    def on_video_select(self, event):
        if not self.prev_videos_listbox.curselection():
            return
        index = self.prev_videos_listbox.curselection()[0]
        self.video_path = self.prev_videos[index]
        self.status_label.config(text="Status: Processando vídeo")
        self.process_thread = threading.Thread(target=self.process_video)
        self.process_thread.start()

    def save_video_info(self):
        with open("video_info.json", "w") as f:
            json.dump({"video_paths": self.prev_videos}, f)

    def process_video(self):
        self.temp_dir = tempfile.mkdtemp()  # Cria um diretório temporário seguro
        frame_paths = []

        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            self.status_label.config(text="Status: Erro ao abrir vídeo")
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(min(cap.get(cv2.CAP_PROP_FRAME_COUNT), 10 * fps))
        frame_interval = int(fps / 24)  # Capturar 24 frames por segundo

        for i in range(frame_count):
            ret, frame = cap.read()
            if not ret:
                break

            if i % frame_interval == 0:
                frame_path = os.path.join(self.temp_dir, f'frame_{i}.png')
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                img.save(frame_path, 'PNG')
                frame_paths.append(frame_path)

        cap.release()
        self.set_wallpaper_video(frame_paths)

    def set_wallpaper_video(self, frame_paths):
        self.running = True
        self.status_label.config(text="Status: Exibindo vídeo")
        while self.running:
            for frame_path in frame_paths:
                if not self.running:
                    break
                ctypes.windll.user32.SystemParametersInfoW(20, 0, frame_path, 3)
                time.sleep(self.speed_var.get())
        self.status_label.config(text="Status: Não exibindo nada")

    def set_wallpaper_image(self, image_path):
        self.stop_wallpaper()
        ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)
        self.status_label.config(text="Status: Exibindo imagem de fundo")

    def stop_wallpaper(self):
        self.running = False
        ctypes.windll.user32.SystemParametersInfoW(20, 0, None, 3)
        self.status_label.config(text="Status: Não exibindo nada")
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir)

class TimerTab:
    def __init__(self, notebook):
        self.timer_tab = ttk.Frame(notebook)
        notebook.add(self.timer_tab, text="Temporizador")

        self.label = tk.Label(self.timer_tab, text="Defina o tempo em segundos:")
        self.label.pack()

        self.time_var = tk.IntVar()
        self.time_entry = tk.Entry(self.timer_tab, textvariable=self.time_var)
        self.time_entry.pack()

        self.action_var = tk.StringVar(value="link")
        self.label = tk.Label(self.timer_tab, text="link ou arquivo:")
        self.label.pack()
        self.link_entry = tk.Entry(self.timer_tab, text="Link ou Caminho do Arquivo")
        self.link_entry.pack()

        self.open_link_radio = tk.Radiobutton(self.timer_tab, text="Abrir Link", variable=self.action_var, value="link")
        self.open_link_radio.pack(anchor=tk.W)

        self.open_file_radio = tk.Radiobutton(self.timer_tab, text="Abrir Arquivo", variable=self.action_var, value="file")
        self.open_file_radio.pack(anchor=tk.W)

        self.start_button = tk.Button(self.timer_tab, text="Iniciar Temporizador", command=self.start_timer)
        self.start_button.pack()

    def start_timer(self):
        seconds = self.time_var.get()
        action = self.action_var.get()
        path = self.link_entry.get()

        if seconds <= 0 or not path:
            messagebox.showwarning("Aviso", "Tempo ou ação inválida.")
            return

        self.timer_thread = threading.Thread(target=self.run_timer, args=(seconds, action, path))
        self.timer_thread.start()

    def run_timer(self, seconds, action, path):
        time.sleep(seconds)
        if action == "link":
            webbrowser.open(path)
        elif action == "file":
            os.startfile(path)

class Application:
    def __init__(self, root):
        self.root = root
        self.root.title("VAL PAPER ENGINE")
        self.root.resizable(False, False)
        self.root.iconbitmap(os.path.abspath("icob.ico"))
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=1, fill="both")
        
        self.video_player = VideoPlayer(self.notebook)
        self.clock_overlay = ClockOverlay(self.notebook)
        self.timer_tab = TimerTab(self.notebook)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.video_player.stop_wallpaper()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = Application(root)
    root.mainloop()
