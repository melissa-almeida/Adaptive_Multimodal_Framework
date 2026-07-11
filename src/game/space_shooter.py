import pygame
import random

class SpaceShooter:
    def __init__(self):
        pygame.init()
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Multimodal Testbed Space Shooter")
        self.clock = pygame.time.Clock()

        # is_running now only controls whether the PROGRAM keeps running.
        # It stays True even after the player dies — only an explicit
        # quit (Q / ESC / closing the window) sets it to False.
        self.is_running = True

        # game_over is the "player is dead, showing Game Over screen" state.
        self.game_over = False

        self.font = pygame.font.SysFont(None, 36)
        self.big_font = pygame.font.SysFont(None, 64)

        # "PLAY AGAIN" button rectangle (used for mouse click detection)
        button_width, button_height = 220, 60
        self.play_again_rect = pygame.Rect(
            self.screen_width // 2 - button_width // 2,
            self.screen_height // 2 + 40,
            button_width,
            button_height
        )

        self._reset_state()

    def _reset_state(self):
        """Reset all gameplay state to start a fresh run."""
        self.player_width = 50
        self.player_height = 40
        self.player_x = self.screen_width // 2
        self.player_y = self.screen_height - 70
        self.player_speed = 7

        self.shield_active = False
        self.shield_duration = 0

        self.bullets = []
        self.enemies = []
        self.spawn_timer = 0
        self.score = 0
        self.game_over = False

    def restart(self):
        """Public method to start a new run after Game Over."""
        self._reset_state()

    def spawn_enemy(self):
        x = random.randint(0, self.screen_width - 40)
        self.enemies.append(pygame.Rect(x, 0, 40, 30))

    def is_play_again_clicked(self, mouse_pos):
        """Call this from main.py when a mouse click event happens."""
        return self.game_over and self.play_again_rect.collidepoint(mouse_pos)

    def update(self, control_actions):
        # If the player is dead, freeze gameplay entirely until restart.
        if self.game_over:
            return

        self.player_x += control_actions['move_x'] * self.player_speed
        self.player_x = max(0, min(self.screen_width - self.player_width, self.player_x))

        if control_actions['fire']:
            if len(self.bullets) < 5:
                bullet = pygame.Rect(self.player_x + self.player_width//2 - 2, self.player_y, 5, 10)
                self.bullets.append(bullet)
        if control_actions['shield'] and not self.shield_active:
            self.shield_active = True
            self.shield_duration = 60
        if self.shield_active:
            self.shield_duration -= 1
            if self.shield_duration <= 0:
                self.shield_active = False
        for bullet in self.bullets[:]:
            bullet.y -= 10
            if bullet.y < 0:
                self.bullets.remove(bullet)
        self.spawn_timer += 1
        if self.spawn_timer > 30:
            self.spawn_enemy()
            self.spawn_timer = 0
        for enemy in self.enemies[:]:
            enemy.y += 4
            if enemy.y > self.screen_height:
                self.enemies.remove(enemy)
            player_rect = pygame.Rect(self.player_x, self.player_y, self.player_width, self.player_height)
            if enemy.colliderect(player_rect):
                if self.shield_active:
                    self.enemies.remove(enemy)
                    self.score += 5
                else:
                    print(f"\n¡Spaceship destroyed! Final score: {self.score}\n")
                    self.game_over = True
                    return
            for bullet in self.bullets[:]:
                if enemy.colliderect(bullet):
                    if bullet in self.bullets: self.bullets.remove(bullet)
                    if enemy in self.enemies: self.enemies.remove(enemy)
                    self.score += 10
                    break

    def render(self):
        self.screen.fill((10, 15, 30))
        self._draw_ship()
        if self.shield_active:
            pygame.draw.circle(self.screen, (0, 150, 255), (int(self.player_x + self.player_width//2), int(self.player_y + self.player_height//2)), 40, 3)
        for bullet in self.bullets:
            self._draw_bullet(bullet)
        for enemy in self.enemies:
            self._draw_enemy(enemy)

        score_text = self.font.render(f"SCORE: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))

        if self.game_over:
            self._render_game_over_overlay()

        pygame.display.flip()

    def _draw_ship(self):
        """Draws a stylized fighter-jet-like ship instead of a plain rectangle."""
        x, y = self.player_x, self.player_y
        w, h = self.player_width, self.player_height
        cx = x + w / 2  # center x

        hull_color = (60, 220, 180)
        hull_edge = (200, 255, 240)
        wing_color = (30, 150, 130)
        cockpit_color = (150, 235, 255)
        flame_outer = (255, 170, 40)
        flame_inner = (255, 235, 120)

        # Engine flame (drawn first, so the hull overlaps its base)
        flicker = random.randint(-3, 3)
        flame_points = [
            (cx - 7, y + h - 2),
            (cx + 7, y + h - 2),
            (cx, y + h + 14 + flicker),
        ]
        pygame.draw.polygon(self.screen, flame_outer, flame_points)
        inner_flame_points = [
            (cx - 3, y + h - 2),
            (cx + 3, y + h - 2),
            (cx, y + h + 8 + flicker // 2),
        ]
        pygame.draw.polygon(self.screen, flame_inner, inner_flame_points)

        # Side wings (swept back triangles)
        left_wing = [(x, y + h), (x + w * 0.32, y + h * 0.45), (x + w * 0.32, y + h)]
        right_wing = [(x + w, y + h), (x + w * 0.68, y + h * 0.45), (x + w * 0.68, y + h)]
        pygame.draw.polygon(self.screen, wing_color, left_wing)
        pygame.draw.polygon(self.screen, wing_color, right_wing)
        pygame.draw.polygon(self.screen, hull_edge, left_wing, width=1)
        pygame.draw.polygon(self.screen, hull_edge, right_wing, width=1)

        # Main hull (nose pointing up)
        hull_points = [
            (cx, y),                      # nose tip
            (x + w * 0.72, y + h * 0.55),
            (x + w * 0.62, y + h),
            (x + w * 0.38, y + h),
            (x + w * 0.28, y + h * 0.55),
        ]
        pygame.draw.polygon(self.screen, hull_color, hull_points)
        pygame.draw.polygon(self.screen, hull_edge, hull_points, width=2)

        # Cockpit
        pygame.draw.ellipse(self.screen, cockpit_color, (cx - 5, y + h * 0.28, 10, 14))

    def _draw_bullet(self, bullet):
        """Glowing laser bolt instead of a flat rectangle."""
        cx = bullet.x + bullet.width // 2
        pygame.draw.line(self.screen, (255, 255, 150),
                          (cx, bullet.y), (cx, bullet.y + bullet.height), 2)
        pygame.draw.circle(self.screen, (255, 255, 200), (cx, bullet.y), 3)

    def _draw_enemy(self, enemy):
        """Stylized enemy ship (nose pointing down) instead of a plain rectangle."""
        x, y, w, h = enemy.x, enemy.y, enemy.width, enemy.height
        cx = x + w / 2

        body_color = (220, 60, 60)
        edge_color = (255, 180, 180)
        core_color = (255, 220, 100)

        points = [
            (cx, y + h),                  # nose tip (pointing down)
            (x + w * 0.85, y + h * 0.35),
            (x + w * 0.65, y),
            (x + w * 0.35, y),
            (x + w * 0.15, y + h * 0.35),
        ]
        pygame.draw.polygon(self.screen, body_color, points)
        pygame.draw.polygon(self.screen, edge_color, points, width=1)
        pygame.draw.circle(self.screen, core_color, (int(cx), int(y + h * 0.4)), 3)

    def _render_game_over_overlay(self):
        # Semi-transparent dark overlay so the frozen game is still visible behind it
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        game_over_text = self.big_font.render("GAME OVER", True, (255, 60, 60))
        text_rect = game_over_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 60))
        self.screen.blit(game_over_text, text_rect)

        final_score_text = self.font.render(f"Final Score: {self.score}", True, (255, 255, 255))
        score_rect = final_score_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 15))
        self.screen.blit(final_score_text, score_rect)

        # PLAY AGAIN button
        pygame.draw.rect(self.screen, (0, 200, 100), self.play_again_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), self.play_again_rect, width=2, border_radius=8)
        button_text = self.font.render("PLAY AGAIN", True, (0, 0, 0))
        button_text_rect = button_text.get_rect(center=self.play_again_rect.center)
        self.screen.blit(button_text, button_text_rect)

        hint_text = self.font.render("Press R to restart", True, (200, 200, 200))
        hint_rect = hint_text.get_rect(center=(self.screen_width // 2, self.play_again_rect.bottom + 30))
        self.screen.blit(hint_text, hint_rect)

    def close(self):
        pygame.quit()
