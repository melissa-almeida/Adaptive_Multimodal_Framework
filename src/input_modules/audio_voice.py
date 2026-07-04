import threading
import time
import numpy as np
import sounddevice as sd
import speech_recognition as sr
from collections import deque

class AudioModule:
    def __init__(self, sample_rate=44100, block_size=1024):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.noise_floor = 0.003
        self.max_volume = 0.05
        self.speech_threshold = 0.01
        self.current_volume = 0.0  
        self.audio_confidence = 1.0 
        self.detected_command = "None"   
        self.running = False
        self.stream = None
        self.lock = threading.Lock()
        self.recognizer = sr.Recognizer()
        self.is_speaking = False
        self.speech_buffer = []
        self.silence_blocks_limit = int((self.sample_rate / self.block_size) * 0.5) 
        self.silence_counter = 0  
        self.volume_history = deque(maxlen=int(self.sample_rate / self.block_size) * 2)      

    def calibrate(self):
        print("\n START AUDIO CALIBRATION")
        print("Remain completely silent for 2 seconds to measure the environment...")
        silence_duration = 2.0
        recording = sd.rec(int(silence_duration * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype='float32')
        sd.wait()
        
        chunks = np.array_split(recording, int(silence_duration * 10))
        rms_values = [np.sqrt(np.mean(c**2)) for c in chunks]
        self.noise_floor = np.mean(rms_values)

        self.speech_threshold = self.noise_floor * 3.0
        print(f" Background noise (RMS): {self.noise_floor:.5f}")
        print(f" Voice activation threshold: {self.speech_threshold:.5f}")
        print("\n Say 'FIRE'!")
        time.sleep(0.5)
        
        shout_duration = 2.0
        recording_shout = sd.rec(int(shout_duration * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype='float32')
        sd.wait()
        
        shout_chunks = np.array_split(recording_shout, int(shout_duration * 20))
        max_rms_detected = max([np.sqrt(np.mean(c**2)) for c in shout_chunks])
        
        if max_rms_detected > self.noise_floor:
            self.max_volume = max_rms_detected
        else:
            self.max_volume = self.noise_floor + 0.05
            
        print(f"Maximum volume threshold (RMS): {self.max_volume:.5f}") 
        print(" Successful Calibration\n")

    def _audio_callback(self, indata, frames, time_info, status):
        rms = np.sqrt(np.mean(indata**2))
        self.volume_history.append(rms)

        with self.lock:
            self.current_volume = rms
            current_ambient_noise = min(self.volume_history) if len(self.volume_history) > 0 else self.noise_floor
    
            if current_ambient_noise > self.noise_floor:
                noise_range = self.speech_threshold - self.noise_floor
                penalty = (current_ambient_noise - self.noise_floor) / noise_range if noise_range > 0 else 0
                self.audio_confidence = max(0.1, min(1.0, 1.0 - penalty))
            else:
                self.audio_confidence = 1.0
                
            # buffering the words
            if rms > self.speech_threshold:
                self.is_speaking = True
                self.speech_buffer.append(indata.copy())
                self.silence_counter = 0
            else:
                if self.is_speaking:
                    self.speech_buffer.append(indata.copy())
                    self.silence_counter += 1
                    if self.silence_counter >= self.silence_blocks_limit:
                        full_phrase_audio = np.concatenate(self.speech_buffer)
                        threading.Thread(
                            target=self._process_speech_async, 
                            args=(full_phrase_audio,), 
                            daemon=True
                        ).start()
                        
                        self.speech_buffer = []
                        self.is_speaking = False
                        self.silence_counter = 0

    def _process_speech_async(self, audio_np):
        audio_int16 = (audio_np * 32767).astype(np.int16).tobytes()
        audio_data = sr.AudioData(audio_int16, self.sample_rate, 2)
        try:
            text = self.recognizer.recognize_google(audio_data, language="en-US").lower()
            with self.lock:
                if "fire" in text or "faj" in text or "fi" in text or "re" in text:   
                    self.detected_command = "FIRE"
                elif "shield" in text or "shil" in text or "shee" in text or "shie" in text or "eld" in text:
                    self.detected_command = "SHIELD"
                else:
                    self.detected_command = f"Not a comand: ({text})"
        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            with self.lock:
                self.detected_command = "Connection Error (API)"

    def start(self):
        if self.running:
            return
        self.running = True
        self.stream = sd.InputStream(
            channels=1,
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            callback=self._audio_callback
        )
        self.stream.start()

    def get_audio_data(self):
        with self.lock:
            return self.current_volume, self.vol_normalized, self.audio_confidence, self.current_command

    def stop(self):
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            print("\n\nAudio module stopped")

# Module test
if __name__ == "__main__":
    audio_mod = AudioModule()
    audio_mod.calibrate()
    audio_mod.start()
    try:
        while True:
            vol = audio_mod.current_volume
            conf = audio_mod.audio_confidence
            cmd = audio_mod.detected_command
            n_floor = audio_mod.noise_floor
            m_vol = audio_mod.max_volume

            vol_normalized = ((vol - n_floor) / (m_vol - n_floor)) * 100 if m_vol > n_floor else 0.0
            vol_normalized = min(100.0, max(0.0, vol_normalized))
            
            
            porc = vol_normalized / 100.0  
            bar_length = int(porc * 20)
            bar = "|" * bar_length
            spaces = " " * (20 - bar_length)
         
            print(f"Volumen: [{bar}{spaces}] {vol_normalized:5.1f}% | Confidence Mic: {conf*100:5.1f}% | Command: {cmd}".ljust(90), end='\r')
            time.sleep(0.1)
            

    except KeyboardInterrupt:
        audio_mod.stop()

