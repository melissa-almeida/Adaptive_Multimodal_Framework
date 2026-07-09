import numpy as np
from collections import deque

# It merges asynchronous multimodal variables based on the statistical reliability of the input signals (Camera and Microphone)
class AdaptationEngine:
    def __init__(self, window_size=10):
        self.vision_history = deque(maxlen=window_size)
        self.audio_history = deque(maxlen=window_size)
        self.THRESH_HIGH_VISION = 0.70   
        self.THRESH_LOW_VISION = 0.40    
        self.current_mode = "FULL_MULTIMODAL"
        self.smoothed_move_x = 0.0
        self.alpha_smoothing = 0.25      

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
        # State Machine Transition based on Sustained Trust (Hysteresis)
        if avg_vision_conf >= self.THRESH_HIGH_VISION:
            self.current_mode = "FULL_MULTIMODAL"
        elif self.THRESH_LOW_VISION <= avg_vision_conf < self.THRESH_HIGH_VISION:
            self.current_mode = "ASSISTED_SMOOTHING"
        else:
            self.current_mode = "SAFE_FALLBACK"
        
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