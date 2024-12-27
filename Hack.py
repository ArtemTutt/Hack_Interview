import tkinter as tk
from tkinter import ttk
from tkinter import Label, Button, Text
from tkinter import messagebox
from ttkbootstrap import Style
import pyaudio
import wave
import threading
from openai import OpenAI


# Параметры аудио записи
RATE = 16000  # Частота дискретизации
CHUNK = 1024  # Размер фрейма
CHANNELS = 1  # Количество каналов
FORMAT = pyaudio.paInt16  # Формат аудио
OUTPUT_FILENAME = "output.wav"  # Имя выходного файла

openai = OpenAI(
    api_key="RmuQxcWMGz7rbIWYurA6SrRZzfBR4dal",
    base_url="https://api.deepinfra.com/v1/openai",
)

# Переменная для отслеживания состояния записи
is_recording = False
frames = []


def toggle_recording():
    global is_recording, frames, record_button
    if is_recording:
        # Если запись уже идёт, останавливаем
        is_recording = False
        record_button.config(text="Запись: OFF")
        stop_recording()
    else:
        # Если запись не идёт, начинаем
        is_recording = True
        frames = []
        record_button.config(text="Запись: ON")
        start_recording()


def start_recording():
    global is_recording, frames
    # Инициализация PyAudio
    audio = pyaudio.PyAudio()

    # Создание потока для записи
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

    label.config(text="Идёт запись...")

    # Функция для записи в отдельном потоке
    def record():
        global is_recording, frames
        while is_recording:
            data = stream.read(CHUNK)
            frames.append(data)

        # Остановка и закрытие потока
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Сохранение в файл
        with wave.open(OUTPUT_FILENAME, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b"".join(frames))

        label.config(text="Запись завершена. Распознаётся аудио...")
        recognize_audio()

    # Запуск записи в отдельном потоке
    threading.Thread(target=record).start()


def stop_recording():
    global is_recording
    is_recording = False


def recognize_audio():
    import speech_recognition as sr

    # Инициализация распознавателя
    recognizer = sr.Recognizer()

    # Загрузка аудиофайла и перевод в текст
    with sr.AudioFile(OUTPUT_FILENAME) as source:
        audio_data = recognizer.record(source)

        try:
            # Преобразование аудио в текст
            TEXT = recognizer.recognize_google(audio_data, language="ru-RU")
            label.config(text=f"Ваш вопрос: {TEXT}")
            chatGPTQuick(TEXT)
            chatGPTFull(TEXT)
        except sr.UnknownValueError:
            label.config(text="Не удалось распознать речь.")
        except sr.RequestError as e:
            label.config(text=f"Ошибка сервиса распознавания речи: {e}")


def chatGPTQuick(text):
    # print(f"Запрос к чату был с таким предложением: " + text)
    chat_completion = openai.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        messages=[{"role": "user", "content": text}, {"role": "system", "content": "Concisely respond, limiting your answer to 70 words."}],
    )
    quick_response = chat_completion.choices[0].message.content
    short_text_area.delete("1.0", tk.END)  # Очистить текстовое поле
    short_text_area.insert(tk.END, quick_response)  # Вставить новый текст


def chatGPTFull(text):
    # print(f"Запрос к чату был с таким предложением: " + text)
    chat_completion = openai.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        messages=[{"role": "user", "content": text}, {"role": "system", "content": "Before answering, take a deep breath and think step by step.Your answer should not exceed more than 150 words."}],
    )
    full_response = chat_completion.choices[0].message.content
    full_text_area.delete("1.0", tk.END)  # Очистить текстовое поле
    full_text_area.insert(tk.END, full_response)  # Вставить новый текст


# Создание GUI
root = tk.Tk()
root.title("Hack interview")
root.geometry("1000x800")

# Применение стиля
style = Style(theme="superhero")

# Настройка цветов
PRIMARY_COLOR = "#3498db"  # Blue
SECONDARY_COLOR = "#2ecc71"  # Green
BACKGROUND_COLOR = "#34495e"  # Dark Blue-Gray
TEXT_COLOR = "#ecf0f1"  # Light Gray

style.configure('TLabel', font=('Segoe UI', 12), foreground=TEXT_COLOR)
style.configure('TButton', font=('Segoe UI', 12), background=PRIMARY_COLOR)
style.configure('TFrame', background=BACKGROUND_COLOR)

main_frame = ttk.Frame(root, padding="20 20 20 20")
main_frame.pack(fill=tk.BOTH, expand=True)

# Заголовок
header_label = ttk.Label(main_frame, text="Hack interview", font=('Segoe UI', 24, 'bold'), foreground=PRIMARY_COLOR)
header_label.pack(pady=20)


# Инструкция
label = ttk.Label(main_frame, text="Click the button to start or stop voice recording", wraplength=400)
label.pack(pady=10)

# Кнопка записи
record_button = ttk.Button(main_frame, text="🎙️ Start Recording", style='success.TButton', command=toggle_recording)
record_button.pack(pady=20)

# Текстовое поле для краткого ответа
short_text_label = ttk.Label(main_frame, text="💎 Quick Answer:")
short_text_label.pack(pady=10)
short_text_area = tk.Text(main_frame, height=5, wrap="word", font=('Segoe UI', 12), bg=BACKGROUND_COLOR, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
short_text_area.pack(pady=5, fill=tk.X)

# Текстовое поле для полного ответа
full_text_label = ttk.Label(main_frame, text="📊 Full Analysis:")
full_text_label.pack(pady=10)
full_text_area = tk.Text(main_frame, height=15, wrap="word", font=('Segoe UI', 12), bg=BACKGROUND_COLOR, fg=TEXT_COLOR, insertbackground=TEXT_COLOR)
full_text_area.pack(pady=5, fill=tk.BOTH, expand=True)

# Запуск основного цикла приложения
root.mainloop()