import pygame
import sys
from game.space_shooter import SpaceShooter

def main():
    game = SpaceShooter()
    
    print("--- Start ---")
    print(" - Arrows Left / Right: Move")
    print(" - Space: Fire")
    print(" - S: Shield")
    print("-------------------------")

    while game.is_running:
        control_actions = {
            'move_x': 0,
            'fire': False,
            'shield': False
        }
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.is_running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            control_actions['move_x'] = -1
        if keys[pygame.K_RIGHT]:
            control_actions['move_x'] = 1
        if keys[pygame.K_SPACE]:
            control_actions['fire'] = True
        if keys[pygame.K_s]:
            control_actions['shield'] = True

        game.update(control_actions)
        game.render()
        game.clock.tick(60)

    game.close()
    sys.exit()

if __name__ == "__main__":
    main()