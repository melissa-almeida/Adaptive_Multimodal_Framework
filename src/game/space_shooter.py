import pygame
import random

class SpaceShooter:
    def __init__(self):
        pygame.init()
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Multimodal Testbed - Space Shooter")
        self.clock = pygame.time.Clock()
        self.is_running = True

        # Propiedades del Jugador
        self.player_width = 50
        self.player_height = 40
        self.player_x = self.screen_width // 2
        self.player_y = self.screen_height - 70
        self.player_speed = 7
        
        # Estado del Escudo (Para comando de voz)
        self.shield_active = False
        self.shield_duration = 0

        # Balas y Enemigos
        self.bullets = []
        self.enemies = []
        self.spawn_timer = 0
        self.score = 0

    def spawn_enemy(self):
        x = random.randint(0, self.screen_width - 40)
        self.enemies.append(pygame.Rect(x, 0, 40, 30))

    def update(self, control_actions):
        """
        Actualiza el juego usando un diccionario de acciones genéricas.
        control_actions = {'move_x': -1|0|1, 'fire': True|False, 'shield': True|False}
        """
        # 1. Movimiento (Viene de Pose / Teclado)
        self.player_x += control_actions['move_x'] * self.player_speed
        # Límites de la pantalla
        self.player_x = max(0, min(self.screen_width - self.player_width, self.player_x))

        # 2. Habilidades: Disparo (Viene de Voz / Teclado)
        if control_actions['fire']:
            # Evitar ráfagas infinitas limitando balas en pantalla
            if len(self.bullets) < 5:
                bullet = pygame.Rect(self.player_x + self.player_width//2 - 2, self.player_y, 5, 10)
                self.bullets.append(bullet)

        # 3. Habilidades: Escudo (Viene de Voz / Teclado)
        if control_actions['shield'] and not self.shield_active:
            self.shield_active = True
            self.shield_duration = 60 # Duración en frames (1 segundo a 60fps)

        if self.shield_active:
            self.shield_duration -= 1
            if self.shield_duration <= 0:
                self.shield_active = False

        # Actualizar Balas
        for bullet in self.bullets[:]:
            bullet.y -= 10
            if bullet.y < 0:
                self.bullets.remove(bullet)

        # Actualizar Enemigos
        self.spawn_timer += 1
        if self.spawn_timer > 30: # Aparece un enemigo cada medio segundo aprox
            self.spawn_enemy()
            self.spawn_timer = 0

        for enemy in self.enemies[:]:
            enemy.y += 4
            if enemy.y > self.screen_height:
                self.enemies.remove(enemy)
                
            # Colisión con el jugador
            player_rect = pygame.Rect(self.player_x, self.player_y, self.player_width, self.player_height)
            if enemy.colliderect(player_rect):
                if self.shield_active:
                    self.enemies.remove(enemy)
                    self.score += 5 # Puntos extra por bloquear
                else:
                    print(f"¡Nave destruida! Puntaje final: {self.score}")
                    self.is_running = False

            # Colisión con balas
            for bullet in self.bullets[:]:
                if enemy.colliderect(bullet):
                    if bullet in self.bullets: self.bullets.remove(bullet)
                    if enemy in self.enemies: self.enemies.remove(enemy)
                    self.score += 10
                    break

    def render(self):
        self.screen.fill((10, 15, 30)) # Fondo oscuro espacial

        # Dibujar Jugador
        pygame.draw.rect(self.screen, (0, 255, 150), (self.player_x, self.player_y, self.player_width, self.player_height))
        
        # Dibujar Escudo si está activo
        if self.shield_active:
            pygame.draw.circle(self.screen, (0, 150, 255), (int(self.player_x + self.player_width//2), int(self.player_y + self.player_height//2)), 40, 3)

        # Dibujar Balas
        for bullet in self.bullets:
            pygame.draw.rect(self.screen, (255, 255, 0), bullet)

        # Dibujar Enemigos
        for enemy in self.enemies:
            pygame.draw.rect(self.screen, (255, 50, 50), enemy)

        # Dibujar UI de puntaje
        font = pygame.font.SysFont(None, 36)
        score_text = font.render(f"SCORE: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))

        pygame.display.flip()

    def close(self):
        pygame.quit()