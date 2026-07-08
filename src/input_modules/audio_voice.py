import threading
import torch
import time
import numpy as np
import sounddevice as sd
import speech_recognition as sr
import queue


class AudioModule:
    def __init__(self, sample_rate=16000): 
        self.sample_rate = sample_rate
        self.block_size = 512
        self.r = sr.Recognizer()
        self.lock = threading.Lock()
        self.current_volume = 0.0
        self.vol_normalized = 0.0
        self.audio_confidence = 0.0
        self.current_command = "NONE"
        self.min_rms = 0.001
        self.max_rms = 0.05
        self.audio_queue = queue.Queue()
        self.audio_buffer = []
        self.is_speaking = False
        self.is_recognizing = False
        self.running = False
        self.stream = None

        self.model, self.utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            trust_repo=True
        )
        torch.set_num_threads(1)

    def calibrate(self):
        print("\n START AUDIO CALIBRATION")
        print("Remain completely silent for 2 seconds to measure the environment")
        silence_duration = 2.0
        recording = sd.rec(int(silence_duration * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype='float32')
        sd.wait()
        chunks = np.array_split(recording, int(silence_duration * 10))
        rms_values = [np.sqrt(np.mean(c**2)) for c in chunks]
        self.min_rms = np.mean(rms_values) if rms_values else 0.001

        print(f" Background noise (RMS): {self.min_rms:.5f}")
        print("\n Say a command Fire / Shoot or Shield / Barrier")
        time.sleep(0.5)
        shout_duration = 2.0
        recording_shout = sd.rec(int(shout_duration * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype='float32')
        sd.wait()
        shout_chunks = np.array_split(recording_shout, int(shout_duration * 20))
        rms_shout_values = [np.sqrt(np.mean(c**2)) for c in shout_chunks if len(c) > 0]
        self.max_rms = max(rms_shout_values) if rms_shout_values else 0.05
        if self.max_rms <= self.min_rms:
            self.max_rms = self.min_rms + 0.05
        print(f"Maximum volume threshold (RMS): {self.max_rms:.5f}") 
        print(" Successful Calibration\n")

    def _audio_callback(self, indata, frames, time, status):
        #if status:
            #print(f"Audio Hardware WARNING: {status}")
        self.audio_queue.put((indata[:, 0].copy(), bool(status)))
        
    def _processing_loop(self):
        accumulated_samples = []
        while self.running:
            try:
                raw_chunk, had_status = self.audio_queue.get(timeout=0.1)
                if had_status:
                    print(f"Audio Thread Warning: : {status}")
                accumulated_samples.extend(raw_chunk.tolist())
            except queue.Empty:
                continue
            while len(accumulated_samples) >= self.block_size:
                raw_samples = np.array(accumulated_samples[:self.block_size], dtype=np.float32)
                accumulated_samples = accumulated_samples[self.block_size:]
            # Volume
            rms = np.sqrt(np.mean(raw_samples**2))
            if self.max_rms > self.min_rms:
                norm = ((rms - self.min_rms) / (self.max_rms - self.min_rms)) * 100.0
                vol_norm = max(0.0, min(100.0, norm))
            else:
                vol_norm = 0.0
                
            # Silero VAD
            input_tensor = torch.from_numpy(raw_samples)
            speech_prob = self.model(input_tensor, self.sample_rate).item()
            
            with self.lock:
                self.current_volume = rms
                self.vol_normalized = vol_norm
                self.audio_confidence = speech_prob
            
            # Segmentation of the buffer voice
                if speech_prob > 0.25:
                    if not self.is_speaking:
                        self.is_speaking = True
                    self.audio_buffer.extend(raw_samples.tolist())
                else:
                    if self.is_speaking:
                        if len(self.audio_buffer) > self.sample_rate * 0.5:
                            audio_data = np.array(self.audio_buffer, dtype=np.float32)
                            if not self.is_recognizing:
                                self.is_recognizing = True
                                threading.Thread(target=self._recognize_speech, args=(audio_data,), daemon=True).start()
                        self.audio_buffer = []
                        self.is_speaking = False

    def _recognize_speech(self, float32_samples):
        try:
            audio_int16 = np.int16(np.clip(float32_samples, -1.0, 1.0) * 32767)
            byte_data = audio_int16.tobytes()
            audio_obj = sr.AudioData(byte_data, self.sample_rate, sample_width=2)
            # For offline operation -> recognize_Sphinx 
            command = self.r.recognize_google(audio_obj, language="en-US").lower().strip()
            print(f"Recognized command: {command}")
            
            with self.lock:
                if ("fire" in command 
                    or "faj" in command 
                    or "fai" in command 
                    or "ire" in command
                    or "shoot" in command
                    or "shoots" in command
                    or "shut" in command
                    or "shot" in command
                    or "shit" in command
                    or "shoe" in command
                    or "shoo" in command
                    or "chu" in command
                    or "choot" in command
                    or "shute" in command
                    or "shooting" in command
                    ):   
                    self.current_command = "Command: FIRE / SHOOT"
                elif ( "shield" in command
                        or "shil" in command
                        or "shee" in command
                        or "shie" in command
                        or "eld" in command
                        or "barrier" in command
                        or "barier" in command
                        or "barry" in command
                        or "berry" in command
                        or "barria" in command
                        or "bari" in command
                        or "rier" in command
                    ):
                    self.current_command = "Command: SHIELD / BARRIER"
                else:
                    self.current_command = f"Not a command: {command}"
        except sr.UnknownValueError:
            with self.lock:
                self.current_command = "NOISE / UNKNOWN"
        except sr.RequestError:
            with self.lock:
                self.current_command = "API Cloud Error"
        finally:
            self.is_recognizing = False

    def start(self):
        if self.running:
            return
        self.running = True
        self.process_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.process_thread.start()
        self.stream = sd.InputStream(
            channels=1,
            samplerate=self.sample_rate,
            blocksize=2048, 
            callback=self._audio_callback
        )
        self.stream.start()

    def stop(self):
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            print("\nAudio module stopped\n")

    def get_audio_data(self):
        with self.lock:
            return self.current_volume, self.vol_normalized, self.audio_confidence, self.current_command
    
# Module test
if __name__ == "__main__":
    audio_mod = AudioModule()
    audio_mod.calibrate()
    audio_mod.start()
    try:
        while True:
            _, vol_norm, conf, cmd = audio_mod.get_audio_data()
            bar_length = 20
            bar_filled = int((vol_norm / 100) * bar_length)
            bar = "|" * bar_filled + " " * (bar_length - bar_filled)      
            print(f"\rVolumen: [{bar}] {vol_norm:5.1f}% | VAD Confidence: {conf * 100:5.1f}% | Command: {cmd}".ljust(95), end='', flush=True)
            time.sleep(0.05)
    except KeyboardInterrupt:
        audio_mod.stop()
