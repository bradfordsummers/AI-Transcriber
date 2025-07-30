import customtkinter as ctk
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import threading
import os
import openai

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.client = None
        self.is_recording = False
        self.frames = []
        self.samplerate = 44100

        self.title("AI Transcriber")
        self.geometry("700x500")

        # Set color theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("green")

        # Main frame
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Title
        self.title_label = ctk.CTkLabel(self.main_frame, text="AI Voice Transcriber", font=ctk.CTkFont(size=30, weight="bold", family="Helvetica"))
        self.title_label.pack(pady=(0, 20))

        # Text box
        self.textbox = ctk.CTkTextbox(self.main_frame, width=400, height=200, wrap="word", font=("Helvetica", 16), corner_radius=10, border_width=2)
        self.textbox.pack(pady=10, padx=10, fill="both", expand=True)

        # Buttons frame
        self.buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.buttons_frame.pack(pady=20)

        # Record button
        self.record_button = ctk.CTkButton(self.buttons_frame, text="Record", command=self.record_button_callback, width=140, height=45, corner_radius=10, font=("Helvetica", 16, "bold"), hover_color="#2E8B57")
        self.record_button.pack(side="left", padx=10)

        # Copy button
        self.copy_button = ctk.CTkButton(self.buttons_frame, text="Copy Text", command=self.copy_text, width=140, height=45, corner_radius=10, font=("Helvetica", 16, "bold"), hover_color="#2E8B57")
        self.copy_button.pack(side="left", padx=10)

        self.setup_openai_client()

    def setup_openai_client(self):
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            dialog = ctk.CTkInputDialog(text="Enter your OpenRouter API Key:", title="OpenRouter API Key")
            api_key = dialog.get_input()
            if api_key:
                os.environ["OPENROUTER_API_KEY"] = api_key
                self.client = openai.OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=api_key
                )
            else:
                self.title_label.configure(text="API Key not provided. Transcription disabled.")
        else:
            self.client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key
            )

    def record_button_callback(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        self.is_recording = True
        self.frames = []
        self.record_button.configure(text="Stop Recording", fg_color="#E53935", hover_color="#C62828")
        threading.Thread(target=self.record_audio, daemon=True).start()

    def stop_recording(self):
        self.is_recording = False
        self.record_button.configure(text="Record", fg_color="#1DB954", hover_color="#2E8B57")
        self.save_recording()

    def record_audio(self):
        with sd.InputStream(samplerate=self.samplerate, channels=1, dtype='int16') as stream:
            while self.is_recording:
                self.frames.append(stream.read(1024)[0])

    def save_recording(self):
        if self.frames:
            recording = np.concatenate(self.frames, axis=0)
            write("output.wav", self.samplerate, recording)
            print("Recording saved to output.wav")
            self.transcribe_audio("output.wav")

    def transcribe_audio(self, file_path):
        if not self.client:
            return
        
        self.title_label.configure(text="Transcribing...")
        try:
            with open(file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                  model="openai/whisper-large-v3",
                  file=audio_file
                )
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", transcript.text)
            self.title_label.configure(text="AI Voice Transcriber")
        except Exception as e:
            self.title_label.configure(text=f"Error: {e}")


    def copy_text(self):
        self.clipboard_clear()
        self.clipboard_append(self.textbox.get("1.0", "end-1c"))

if __name__ == "__main__":
    app = App()
    app.mainloop()