import tkinter as tk
from ttkbootstrap import Style, ttk
import pyaudio
import wave
import threading
import speech_recognition as sr
from openai import OpenAI
import os
from tkinter.font import Font


# Audio recording parameters
RATE = 16000
CHUNK = 1024
CHANNELS = 1
FORMAT = pyaudio.paInt16
OUTPUT_FILENAME = "output.wav"

# OpenAI client initialization
openai = OpenAI(
    api_key="RmuQxcWMGz7rbIWYurA6SrRZzfBR4dal",
    base_url="https://api.deepinfra.com/v1/openai",
)

# Global variables
is_recording = False
frames = []

class MultiPageApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI-Powered Role Assistant")
        self.geometry("1000x800")
        self.style = Style(theme="darkly")
        self.frames = {}
        self.current_role = None

        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        for PageClass in (MainPage, FrontendPage, BackendPage, PMPage, QAEngineerPage, DevOpsPage, DataAnalystPage):
            page = PageClass(container, self)
            self.frames[PageClass] = page
            page.grid(row=0, column=0, sticky="nsew")

        self.show_frame(MainPage)

    def show_frame(self, page_class):
        frame = self.frames[page_class]
        frame.tkraise()
        if page_class != MainPage:
            self.current_role = page_class.__name__
        else:
            self.current_role = None

class MainPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        main_container = ttk.Frame(self)
        main_container.pack(expand=True, fill="both")

        center_frame = ttk.Frame(main_container)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        title_label = ttk.Label(
            center_frame,
            text="Hack Interview",
            font=("Helvetica", 28, "bold"),
            bootstyle="inverse-primary"
        )
        title_label.pack(pady=(0, 30))

        buttons_info = [
            ("Frontend Developer", FrontendPage, "info"),
            ("Backend Developer", BackendPage, "success"),
            ("Project Manager", PMPage, "warning"),
            ("QA Engineer", QAEngineerPage, "danger"),
            ("DevOps Engineer", DevOpsPage, "primary"),
            ("Data Analyst", DataAnalystPage, "secondary")
        ]
        # style = ttk.Style()
        # style.configure("TButton", font=("Arial", 12))

        for text, page, style in buttons_info:
            btn = ttk.Button(
                center_frame,
                text=text,
                command=lambda p=page: self.controller.show_frame(p),
                bootstyle=f"{style}-outline",
                width=35,

            )
            btn.pack(pady=10)

        ttk.Separator(center_frame, bootstyle="info").pack(fill="x", pady=20)

        footer_label = ttk.Label(
            center_frame,
            text="Select a role to explore more",
            font=("Helvetica", 12),
            bootstyle="secondary"
        )
        footer_label.pack(pady=(0, 20))

class RolePage(ttk.Frame):
    def __init__(self, parent, controller, title):
        super().__init__(parent)
        self.controller = controller
        self.title = title

        content_frame = ttk.Frame(self, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)

        label = ttk.Label(content_frame, text=title, font=("Helvetica", 24, "bold"))
        label.pack(pady=20)

        description = ttk.Label(
            content_frame,
            text=f"Ask questions related to {title} role.",
            wraplength=600
        )
        description.pack(pady=20)

        self.status_label = ttk.Label(content_frame, text="Press the button to start recording")
        self.status_label.pack(pady=10)

        self.record_button = ttk.Button(content_frame, text="Record: OFF", command=self.toggle_recording)
        self.record_button.pack(pady=10)

        short_text_label = ttk.Label(content_frame, text="Quick Answer:")
        short_text_label.pack(pady=5)
        self.short_text_area = tk.Text(content_frame, height=5, wrap="word", font=('Helvetica', 12))
        self.short_text_area.pack(pady=5, fill=tk.X, expand=True)

        full_text_label = ttk.Label(content_frame, text="Detailed Answer:")
        full_text_label.pack(pady=5)
        self.full_text_area = tk.Text(content_frame, height=10, wrap="word", font=('Helvetica', 12))
        self.full_text_area.pack(pady=5, fill=tk.BOTH, expand=True)

        back_btn = ttk.Button(
            content_frame,
            text="Back to Main Menu",
            command=lambda: controller.show_frame(MainPage),
            style="secondary.TButton"
        )
        back_btn.pack(pady=20)

    def toggle_recording(self):
        global is_recording, frames
        if is_recording:
            is_recording = False
            self.record_button.config(text="Record: OFF")
            self.stop_recording()
        else:
            is_recording = True
            frames = []
            self.record_button.config(text="Record: ON")
            self.start_recording()

    def start_recording(self):
        global is_recording, frames
        audio = pyaudio.PyAudio()
        stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        self.status_label.config(text="Recording...")

        def record():
            global is_recording, frames
            while is_recording:
                data = stream.read(CHUNK)
                frames.append(data)

            stream.stop_stream()
            stream.close()
            audio.terminate()

            with wave.open(OUTPUT_FILENAME, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b"".join(frames))

            self.status_label.config(text="Recording finished. Recognizing audio...")
            self.recognize_audio()

        threading.Thread(target=record).start()

    def stop_recording(self):
        global is_recording
        is_recording = False

    def recognize_audio(self):
        recognizer = sr.Recognizer()
        with sr.AudioFile(OUTPUT_FILENAME) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language="ru-RU")
                self.status_label.config(text=f"Your question: {text}")
                self.chatGPTQuick(text)
                self.chatGPTFull(text)
            except sr.UnknownValueError:
                self.status_label.config(text="Could not recognize speech.")
            except sr.RequestError as e:
                self.status_label.config(text=f"Speech recognition service error: {e}")

    def get_role_prompt(self):
        prompts = {
            "FrontendPage": "You are an expert frontend developer. Focus on HTML, CSS, JavaScript, and modern frontend frameworks.",
            "BackendPage": "You are an expert backend developer. Focus on server-side languages, databases, and API development.",
            "PMPage": "You are an experienced project manager. Focus on project planning, team management, and agile methodologies.",
            "QAEngineerPage": "You are a skilled QA engineer. Focus on testing methodologies, automation, and quality assurance practices.",
            "DevOpsPage": "You are a DevOps specialist. Focus on CI/CD, infrastructure as code, and cloud technologies.",
            "DataAnalystPage": "You are a data analyst expert. Focus on data analysis, visualization, and statistical methods."
        }
        return prompts.get(self.__class__.__name__, "You are a helpful AI assistant.")

    def chatGPTQuick(self, text):
        role_prompt = self.get_role_prompt()
        chat_completion = openai.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            messages=[
                {"role": "system", "content": f"{role_prompt} Concisely respond, limiting your answer to 70 words."},
                {"role": "user", "content": text}
            ],
        )
        quick_response = chat_completion.choices[0].message.content
        self.short_text_area.delete("1.0", tk.END)
        self.short_text_area.insert(tk.END, quick_response)

    def chatGPTFull(self, text):
        role_prompt = self.get_role_prompt()
        chat_completion = openai.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            messages=[
                {"role": "system", "content": f"{role_prompt} Before answering, take a deep breath and think step by step. Your answer should not exceed more than 150 words."},
                {"role": "user", "content": text}
            ],
        )
        full_response = chat_completion.choices[0].message.content
        self.full_text_area.delete("1.0", tk.END)
        self.full_text_area.insert(tk.END, full_response)

class FrontendPage(RolePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Frontend Developer")

class BackendPage(RolePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Backend Developer")

class PMPage(RolePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Project Manager")

class QAEngineerPage(RolePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "QA Engineer")

class DevOpsPage(RolePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "DevOps Engineer")

class DataAnalystPage(RolePage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Data Analyst")

if __name__ == "__main__":
    app = MultiPageApp()
    app.mainloop()

