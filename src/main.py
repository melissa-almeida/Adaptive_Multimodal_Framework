import pygame
import sys
import cv2
import os
from game.space_shooter import SpaceShooter
from input_modules.vision_pose import PoseTracker
from input_modules.audio_voice import AudioModule
from adaptation.adaptation_engine import AdaptationEngine
pygame.time.get_ticks()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

def main():
    pygame.init()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No webcam detected")
        return
    pose_tracker = PoseTracker()
    ret, frame = cap.read()
    if ret:
        try:
            pose_tracker.process_frame(frame) 
        except AttributeError:
            pass
    audio_mod = AudioModule()
    audio_mod.calibrate()
    game = SpaceShooter()
    adaptation_engine = AdaptationEngine()
    audio_mod.start()
    clock = pygame.time.Clock()
    running = True
    display_cmd = "NONE"
    cmd_display_until = 0

    while running and game.is_running:
        ret, frame = cap.read()
        if not ret:
            print("Error to capture frame")
            break
        
        action, vision_confidence = pose_tracker.process_frame(frame)       
        _, audio_vol_norm, audio_confidence, audio_cmd = audio_mod.get_audio_data()
        
        control_actions = {
            'move_x': 0,
            "LEFT": False,
            "RIGHT": False,
            "FIRE": False,
            "SHIELD": False,
            'fire': False,
            'shield': False
        }
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            control_actions['fire'] = True
            control_actions['FIRE'] = True
        if keys[pygame.K_s]:
            control_actions['shield'] = True
            control_actions['SHIELD'] = True
        if keys[pygame.K_LEFT]:
            control_actions['move_x'] = -1
            control_actions['LEFT'] = True
        if keys[pygame.K_RIGHT]:
            control_actions['move_x'] = 1
            control_actions['RIGHT'] = True

        adapted_actions, adaptation_meta = adaptation_engine.adapt(
            control_actions=control_actions,
            vision_action=action,
            vision_confidence=vision_confidence,
            audio_vol_norm=audio_vol_norm,
            audio_confidence=audio_confidence,
            audio_cmd=audio_cmd
        )

        if adaptation_meta['consume_command']:
            with audio_mod.lock:
                audio_mod.current_command = "NONE"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    running = False
       
        game.update(adapted_actions)
        game.render()

        if not game.is_running:
            break
        h, w, _ = frame.shape
        current_ticks = pygame.time.get_ticks()
        
        if audio_cmd != "NONE":
            display_cmd = audio_cmd
            cmd_display_until = current_ticks + 2000  
        elif current_ticks > cmd_display_until:
            display_cmd = audio_cmd

        if "FIRE" in display_cmd or "SHIELD" in display_cmd:
            cmd_color = (0, 255, 0)       
        elif "NONE" in display_cmd:
            cmd_color = (0, 0, 255)   
        else: # UNKNOWN / NOISE
            cmd_color = (0, 255, 255)

        cv2.putText(frame, f"{display_cmd}", (10, 75), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, cmd_color, 2)
    
        if audio_confidence < 0.40:  
            ac_color = (0, 0, 255)
        else:
            ac_color = (0, 250, 0)

        cv2.putText(frame, f"Confidence Microphone: {audio_confidence :.2f}%", (w - 260, 75), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, ac_color, 2)  

        current_mode = adaptation_meta['mode']
        if current_mode == "FULL_MULTIMODAL":
            mode_color_bgr = (0, 255, 0)     
        elif current_mode == "ASSISTED_SMOOTHING":
            mode_color_bgr = (0, 255, 255)   
        else: #SAFE_FALLBACK
            mode_color_bgr = (0, 0, 255)     

        cv2.putText(frame, f"MODE: {current_mode}", (15, 110), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, mode_color_bgr, 2, cv2.LINE_AA)
        
        if adaptation_meta['cross_modal_trigger']:
            cv2.putText(frame, "EMERGENCY SHIELD ACTIVE!", (15, 140), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2, cv2.LINE_AA)
        
        cv2.imshow("Debug Camera View", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            running = False

        clock.tick(60)

    cap.release()
    pose_tracker.close()
    audio_mod.stop()
    cv2.destroyAllWindows()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
