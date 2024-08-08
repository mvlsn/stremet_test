import streamlit as st
import threading
import av
from streamlit_webrtc import WebRtcMode, webrtc_streamer
import speech_recognition as sr
import io
import time
from collections import deque

st.title("AI Interviewer")

# Initialize the recognizer
recognizer = sr.Recognizer()

def speech_to_text(audio_file):
    """Convert speech in an audio file to text using Google Speech Recognition."""
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
    
    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Speech recognition could not understand the audio"
    except sr.RequestError as e:
        return f"Could not request results from speech recognition service; {e}"

def save_and_transcribe(frames, sample_rate, filename="output_chunk.wav"):
    """Save audio frames to a file and transcribe the text."""
    wf = wave.open(filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    transcription = speech_to_text(filename)
    st.session_state.transcription = transcription

async def audio_frame_callback(frame: av.AudioFrame):
    """Handle incoming audio frames from WebRTC."""
    with frames_deque_lock:
        frames_deque.append(frame)

def webrtc_callback(frame: av.VideoFrame):
    """Handle incoming video frames from WebRTC (not used currently)."""
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
text_output = st.empty()

# Define lock and deque for frame management
frames_deque_lock = threading.Lock()
frames_deque = deque()

# Initialize session state for transcription
if 'transcription' not in st.session_state:
    st.session_state.transcription = ""

# Display real-time transcription
while True:
    if webrtc_ctx.state.playing:
        if len(frames_deque) > 0:
            status_indicator.write("Running. Say something!")
            # Combine and process audio frames if necessary
        else:
            status_indicator.write("No frame arrived.")
        time.sleep(1)  # Adjust as necessary to balance between performance and responsiveness
    else:
        status_indicator.write("Stopped.")
        break
