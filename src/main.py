import pygame
import sys
import cv2
from game.space_shooter import SpaceShooter
from input_modules.vision_pose import PoseTracker

def main():
    game = SpaceShooter()
    pose_tracker = PoseTracker()
    print("Start...")

    while game.is_running:
        success, camera_frame = pose_tracker.update()
        tilt = pose_tracker.current_tilt
        confidence = pose_tracker.confidence_score
        control_actions = {
            'move_x': 0,
            'fire': False,
            'shield': False
        }
        direction_text = ""
        if confidence > 0.4:
            if tilt < -0.3:
                control_actions['move_x'] = -1  
                direction_text = "LEFT"
            elif tilt > 0.3:
                control_actions['move_x'] = 1   
                direction_text = "RIGHT"
        else:
            direction_text = "LOW CONFIDENCE"
            # Aquí es donde el profesor verá la magia en el futuro: 
            # "Baja confianza -> activar filtros preventivos o modo seguro"
            pass
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.is_running = False

        # manual keyboard controls for testing (just in case)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            control_actions['fire'] = True
        if keys[pygame.K_s]:
            control_actions['shield'] = True
        if keys[pygame.K_LEFT]:
            control_actions['move_x'] = -1
        if keys[pygame.K_RIGHT]:
            control_actions['move_x'] = 1

        game.update(control_actions)
        game.render()

        if success and camera_frame is not None:
            status_color = (0, 255, 0) if confidence > 0.4 else (0, 0, 255)
            cv2.putText(camera_frame, f"Cam Confidence: {confidence:.2f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            if direction_text == "LOW CONFIDENCE":  #red
                cv2.putText(camera_frame, direction_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            elif direction_text in ["MOVE: LEFT", "MOVE: RIGHT"]: #yellow/cyan
                cv2.putText(camera_frame, direction_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)
            else: #gray 
                cv2.putText(camera_frame, direction_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 1)
            cv2.imshow("Debug Camera View", camera_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        game.clock.tick(60)

    pose_tracker.close()
    cv2.destroyAllWindows()
    game.close()
    sys.exit()

if __name__ == "__main__":
    main()
