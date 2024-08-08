import streamlit as st
import threading
import pyaudio
import wave
import time
import numpy as np
import av
from streamlit_webrtc import WebRtcMode, webrtc_streamer
import speech_recognition as sr
import io

st.title("AI Interviewer")

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
    print("Transcribed text:", text)

# Function to transcribe speech from an audio file
def speech_to_text(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
    
    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Speech recognition could not understand the audio"
    except sr.RequestError as e:
        return f"Could not request results from speech recognition service; {e}"

# WebRTC callback function for handling audio frames
async def audio_frame_callback(frame: av.AudioFrame):
    with frames_deque_lock:
        frames_deque.append(frame)

def webrtc_callback(frame: av.VideoFrame):
    # Handle video frames if needed
    pass

# WebRTC configuration
webrtc_ctx = webrtc_streamer(
    key="webcam-stream",
    mode=WebRtcMode.SENDRECV,
    audio_frame_callback=audio_frame_callback,
    video_frame_callback=webrtc_callback,
    media_stream_constraints={"video": True, "audio": True},
)

status_indicator = st.empty()
status_indicator.write("Loading...")
text_output = st.empty()

# Define lock and deque for frame management
frames_deque_lock = threading.Lock()
frames_deque = []

# Main execution
get_input_device_info()  # Check available input devices and their properties

# Record for the length of the video
stop_event = threading.Event()
frames = []
audio_thread = threading.Thread(target=record_audio, args=(frames,))
audio_thread.start()

# WebRTC will handle video streaming, so no need for a separate capture function
while True:
    if webrtc_ctx.state.playing:
        if frames:
            st.write("Running. Say something!")
            # Combine and process audio frames if necessary
        else:
            st.write("No frame arrived.")
        time.sleep(1)  # Adjust as necessary to balance between performance and responsiveness
    else:
        st.write("Stopped.")
        break

audio_thread.join()  # Wait for the audio recording to finish
