import pygame
import sys
from game.space_shooter import SpaceShooter

def main():
    # Inicializar el entorno de pruebas (el juego)
    game = SpaceShooter()
    
    print("--- Testbed Iniciado ---")
    print("Controles del teclado (Simulación):")
    print(" - Flechas Izquierda / Derecha: Moverse")
    print(" - Espacio: Disparar (Voz simulada)")
    print(" - S: Activar Escudo (Voz simulada)")
    print("-------------------------")

    while game.is_running:
        # Diccionario de acciones por defecto (Ninguna acción activa)
        control_actions = {
            'move_x': 0,
            'fire': False,
            'shield': False
        }

        # Capturar eventos nativos de salida
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.is_running = False

        # SIMULACIÓN: Leer teclado y traducirlo al formato del Framework
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            control_actions['move_x'] = -1
        if keys[pygame.K_RIGHT]:
            control_actions['move_x'] = 1
            
        # Para acciones tipo disparo/escudo usamos eventos o pulsaciones discretas
        if keys[pygame.K_SPACE]:
            control_actions['fire'] = True
        if keys[pygame.K_s]:
            control_actions['shield'] = True

        # Pasar las acciones calculadas al bucle del juego
        game.update(control_actions)
        game.render()
        
        # Forzar 60 cuadros por segundo constantes
        game.clock.tick(60)

    game.close()
    sys.exit()

if __name__ == "__main__":
    main()