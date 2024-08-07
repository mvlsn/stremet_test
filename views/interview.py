import streamlit as st
import pyaudio
import wave
import io
import threading
import time
import speech_recognition as sr

def get_input_device_info():
    audio = pyaudio.PyAudio()
    devices = []
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        devices.append({
            "index": i,
            "name": info['name'],
            "channels": info['maxInputChannels']
        })
    audio.terminate()
    return devices

def record_audio(file, sample_rate=44100, chunk=4096, channels=1, duration=5):
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

    st.write("Recording audio...")
    frames = []
    start_time = time.time()
    
    while time.time() - start_time < duration:
        try:
            data = stream.read(chunk, exception_on_overflow=False)
            frames.append(data)
        except IOError as e:
            st.write(f"Error recording: {e}")
            continue
    
    st.write("Finished recording audio.")
    
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    save_and_transcribe(frames, sample_rate, file)

def save_and_transcribe(frames, sample_rate, filename="output_chunk.wav"):
    wf = wave.open(filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    text = speech_to_text(filename)
    st.write("Transcribed text:", text)

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

def main():
    st.title('Microphone Selection and Audio Recording')

    # Display microphone options
    devices = get_input_device_info()
    mic_options = {device['name']: device['index'] for device in devices}
    
    mic_selected = st.selectbox('Select a Microphone', options=list(mic_options.keys()))
    mic_index = mic_options[mic_selected]

    st.write('Selected Microphone Index:', mic_index)

    # Record audio
    if st.button('Start Recording'):
        st.write("Recording...")
        audio_file = io.BytesIO()  # Use in-memory file
        record_audio(audio_file, duration=5)
        st.write("Audio recorded and saved.")

if __name__ == "__main__":
    main()
