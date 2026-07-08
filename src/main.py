import pygame
import sys
import cv2
import os
from game.space_shooter import SpaceShooter
from input_modules.vision_pose import PoseTracker
from input_modules.audio_voice import AudioModule
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

def main():
    pygame.init()
    game = SpaceShooter()
    pose_tracker = PoseTracker()
    audio_mod = AudioModule()
    audio_mod.calibrate()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: No webcam detected")
        return
    clock = pygame.time.Clock()
    running = True

    audio_mod.start()

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
        if vision_confidence > 0.6:
            if action == "LEFT":
                control_actions['move_x'] = -1  
                control_actions['LEFT'] = True
            elif action == "RIGHT":
                control_actions['move_x'] = 1   
                control_actions['RIGHT'] = True
        else:
            # En el futuro, este bloque decidirá si le cede el 100% del control al módulo de Audio. 
            # "Baja confianza -> activar filtros preventivos o modo seguro"
            # se conectará al adaptation_engine.py
            control_actions['move_x'] = 0

        if "FIRE" in audio_cmd:
            control_actions['FIRE'] = True
            control_actions['fire'] = True
            with audio_mod.lock:
                audio_mod.current_command = "NONE"
        elif "SHIELD" in audio_cmd:
            control_actions['SHIELD'] = True
            control_actions['shield'] = True
            with audio_mod.lock:
                audio_mod.current_command = "NONE"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    running = False

        # manual keyboard controls for testing (temporal)
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

        game.update(control_actions)
        game.render()

        if not game.is_running:
            break
        h, w, _ = frame.shape

        if "FIRE" in audio_cmd or "SHIELD" in audio_cmd:
            cmd_color = (0, 255, 0)       
        elif "NONE" in audio_cmd:
            cmd_color = (0, 0, 255)   
        else: # UNKNOWN / NOISE
            cmd_color = (0, 255, 255)

        #cv2.putText(frame, f"Command: {audio_cmd}", (10, 75), 
        cv2.putText(frame, f"{audio_cmd}", (10, 75), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, cmd_color, 2)

        cv2.putText(frame, f"Confidence Microphone: {audio_confidence :.2f}%", (w - 260, 75), #audio_confidence * 100
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, cmd_color, 2)  #(0 , 250, 0)

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
