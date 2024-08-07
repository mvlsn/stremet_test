import streamlit as st
import anthropic
import speech_recognition as sr
import pyaudio
import wave
import numpy as np
import cv2 as cv
import threading
import time
import moviepy.editor as mp

st.title("AI Interviewer")

import cv2
import threading
import speech_recognition as sr
import pyaudio
import wave
import time

# Initialize the recognizer
recognizer = sr.Recognizer()

# Function to get input device information
def get_input_device_info():
    audio = pyaudio.PyAudio()
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        print(f"Device {i}: {info['name']} - {info['maxInputChannels']} input channels")
    audio.terminate()

# Function to record audio
def record_audio(frames, sample_rate=44100, chunk=4096, channels=1, duration=5):
    audio = pyaudio.PyAudio()
    try:
        stream = audio.open(format=pyaudio.paInt16,
                            channels=channels,
                            rate=sample_rate,
                            input=True,
                            frames_per_buffer=chunk)
    except OSError as e:
        audio.terminate()
        raise RuntimeError(f"Could not open audio stream: {e}")
    
    print("Recording audio...")
    try:
        while not stop_event.is_set():
            start_time = time.time()
            chunk_frames = []
            while time.time() - start_time < duration:
                try:
                    data = stream.read(chunk, exception_on_overflow=False)
                    chunk_frames.append(data)
                except IOError as e:
                    print(f"Error recording: {e}")
                    continue
                if stop_event.is_set():
                    break
            frames.append(b''.join(chunk_frames))
            threading.Thread(target=save_and_transcribe, args=(chunk_frames, sample_rate)).start()
    except Exception as e:
        stream.stop_stream()
        stream.close()
        audio.terminate()
        raise RuntimeError(f"Error during recording: {e}")

    print("Finished recording audio.")

    stream.stop_stream()
    stream.close()
    audio.terminate()

# Function to save and transcribe audio chunk
def save_and_transcribe(frames, sample_rate, filename="output_chunk.wav"):
    wf = wave.open(filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    text = speech_to_text(filename)
    st.title("Transcribed text:", text)

# Function to transcribe speech from an audio file
def speech_to_text(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
    
    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        st.title("Speech recognition could not understand the audio")
    except sr.RequestError as e:
        return f"Could not request results from speech recognition service; {e}"

# Function to handle video capture
def capture_video():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow('Live Video', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set()  # Signal the audio recording thread to stop
            break
    cap.release()
    cv2.destroyAllWindows()

# Main execution
get_input_device_info()  # Check available input devices and their properties

# Record for the length of the video
frames = []
stop_event = threading.Event()
audio_thread = threading.Thread(target=record_audio, args=(frames,))
audio_thread.start()

capture_video()  # Start capturing video

audio_thread.join()  # Wait for the audio recording to finish

