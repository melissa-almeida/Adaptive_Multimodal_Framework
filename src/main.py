import pygame
import sys
import cv2
import os
from game.space_shooter import SpaceShooter
from input_modules.vision_pose import PoseTracker
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    pygame.init()
    game = SpaceShooter()
    pose_tracker = PoseTracker()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No webcam detected")
        return
    clock = pygame.time.Clock()
    running = True

    while running and game.is_running:
        ret, frame = cap.read()
        if not ret:
            print("Error to capture frame")
            break
        
        action, confidence = pose_tracker.process_frame(frame)       
        control_actions = {
            'move_x': 0,
            "LEFT": False,
            "RIGHT": False,
            "FIRE": False,
            "SHIELD": False,
            'fire': False,
            'shield': False
        }
        if confidence > 0.6:
            if action == "LEFT":
                control_actions['move_x'] = -1  
                control_actions['LEFT'] = True
            elif action == "RIGHT":
                control_actions['move_x'] = 1   
                control_actions['RIGHT'] = True
        else:
            # En el futuro, este bloque decidirá si le cede el 100% del control al módulo de Audio. 
            # "Baja confianza -> activar filtros preventivos o modo seguro"
            control_actions['move_x'] = 0

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

        cv2.imshow("Debug Camera View", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            running = False

        clock.tick(60)

    cap.release()
    pose_tracker.close()
    cv2.destroyAllWindows()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
