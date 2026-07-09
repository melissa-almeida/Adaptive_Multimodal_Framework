import numpy as np
from collections import deque
import pygame

# It merges asynchronous multimodal variables based on the statistical reliability of the input signals (Camera and Microphone)
class AdaptationEngine:
    def __init__(self, window_size=15):
        self.vision_history = deque(maxlen=window_size)
        self.audio_history = deque(maxlen=window_size)
        self.DROP_TO_ASSISTED = 0.70
        self.DROP_TO_SAFE = 0.35
        self.RECOVER_TO_ASSISTED = 0.50
        self.RECOVER_TO_FULL = 0.80   
        self.current_mode = "FULL_MULTIMODAL"
        self.smoothed_move_x = 0.0
        self.alpha_smoothing = 0.25      
        self.last_state_change_time = 0
        self.MIN_ASSISTED_DURATION = 1500

    def adapt(self, control_actions, vision_action, vision_confidence, audio_vol_norm, audio_confidence, audio_cmd):
        self.vision_history.append(vision_confidence)
        self.audio_history.append(audio_confidence)
        avg_vision_conf = sum(self.vision_history) / len(self.vision_history)
        avg_audio_conf = sum(self.audio_history) / len(self.audio_history)

        meta = {
            'mode': self.current_mode,
            'avg_vision_conf': avg_vision_conf,
            'avg_audio_conf': avg_audio_conf,
            'consume_command': False,
            'cross_modal_trigger': False
        }
        current_time = pygame.time.get_ticks()
        if self.current_mode == "FULL_MULTIMODAL":
            if avg_vision_conf < self.DROP_TO_ASSISTED:
                self.current_mode = "ASSISTED_SMOOTHING"
                self.last_state_change_time = current_time
        elif self.current_mode == "ASSISTED_SMOOTHING":
            if avg_vision_conf >= self.RECOVER_TO_FULL:
                self.current_mode = "FULL_MULTIMODAL"
                self.last_state_change_time = current_time
            elif avg_vision_conf < self.DROP_TO_SAFE:
                if (current_time - self.last_state_change_time) >= self.MIN_ASSISTED_DURATION:
                    self.current_mode = "SAFE_FALLBACK"
                    self.last_state_change_time = current_time
        elif self.current_mode == "SAFE_FALLBACK":
            if avg_vision_conf >= self.RECOVER_TO_ASSISTED:
                self.current_mode = "ASSISTED_SMOOTHING"
                self.last_state_change_time = current_time
        
        meta['mode'] = self.current_mode
        target_move_x = 0.0

        if self.current_mode == "FULL_MULTIMODAL":      # High reliability
            if vision_action == "LEFT":
                target_move_x = -1.0
            elif vision_action == "RIGHT":
                target_move_x = 1.0
            if control_actions['move_x'] != 0:
                target_move_x = control_actions['move_x']
            self.smoothed_move_x = target_move_x

        elif self.current_mode == "ASSISTED_SMOOTHING":     # Unstable tracking
            if vision_action == "LEFT":
                target_move_x = -0.65  
            elif vision_action == "RIGHT":
                target_move_x = 0.65
            if control_actions['move_x'] != 0:
                target_move_x = control_actions['move_x']
            # EMA equation
            self.smoothed_move_x = (self.alpha_smoothing * target_move_x) + ((1 - self.alpha_smoothing) * self.smoothed_move_x)
            
        elif self.current_mode == "SAFE_FALLBACK":      # Total failure of the visual system
            self.smoothed_move_x = control_actions['move_x']
        
        control_actions['move_x'] = self.smoothed_move_x
        if control_actions['move_x'] < -0.1:
            control_actions['LEFT'] = True
            control_actions['RIGHT'] = False
        elif control_actions['move_x'] > 0.1:
            control_actions['RIGHT'] = True
            control_actions['LEFT'] = False
        else:
            control_actions['LEFT'] = False
            control_actions['RIGHT'] = False

        voice_command_executed = False
        if "FIRE" in audio_cmd:
            control_actions['FIRE'] = True
            control_actions['fire'] = True
            meta['consume_command'] = True
            voice_command_executed = True
        elif "SHIELD" in audio_cmd:
            control_actions['SHIELD'] = True
            control_actions['shield'] = True
            meta['consume_command'] = True
            voice_command_executed = True
            
        # SAFE_FALLBACK + stationary user + sudden spike in acoustic amplitude = Automatic Shield
        if self.current_mode == "SAFE_FALLBACK" and not voice_command_executed:     # Panic Mode
            if audio_vol_norm > 65.0:
                control_actions['SHIELD'] = True
                control_actions['shield'] = True
                meta['cross_modal_trigger'] = True
        return control_actions, meta
    
