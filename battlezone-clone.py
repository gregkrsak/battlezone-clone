import pygame
import asyncio
import random
import platform
import math

# Model: Manages vector lines and CRT effects
class VectorCRTModel:
    def __init__(self):
        self.lines = []  # List of (start, end) tuples
        self.glow_intensity = 1.0
        self.decay_rate = 0.05
        self.flicker = 0.0

    def add_line(self, start, end):
        self.lines.append((start, end))
        if len(self.lines) > 100:  # Increased limit for projectiles
            self.lines.pop(0)

    def update_glow(self, dt):
        self.glow_intensity = max(0.5, self.glow_intensity - self.decay_rate * dt)
        self.flicker = random.uniform(-0.05, 0.05)  # Simulate CRT flicker

    def get_lines(self):
        return self.lines

    def reset_glow(self):
        self.glow_intensity = 1.0

# View: Renders the vector graphics with CRT effects
class VectorCRTView:
    def __init__(self, model, screen):
        self.model = model
        self.screen = screen
        self.font = pygame.font.SysFont("monospace", 16)

    def render_menu(self):
        self.screen.fill((0, 0, 0))
        title = self.font.render("Battlezone: Vector CRT", True, (0, 100, 0))
        controls = [
            "Controls:",
            "W/S: Move Forward/Backward",
            "A/D: Rotate Left/Right",
            "Mouse: Aim",
            "Left Click: Shoot",
            "Q: Quit",
            "Space: Start Game"
        ]
        for i, line in enumerate(controls):
            text = self.font.render(line, True, (50, 50, 50))
            self.screen.blit(text, (300, 200 + i * 20))
        self.screen.blit(title, (320, 150))
        pygame.display.flip()

    def render_game(self, controller):
        self.screen.fill((0, 0, 0))
        # Render ground plane (simple grid)
        for z in range(0, 1000, 100):
            for x in range(-500, 501, 100):
                p1 = self.project([x, 0, z], controller.player_pos, controller.player_angle)
                p2 = self.project([x + 100, 0, z], controller.player_pos, controller.player_angle)
                p3 = self.project([x, 0, z + 100], controller.player_pos, controller.player_angle)
                if p1 and p2:
                    self.model.add_line(p1, p2)
                if p1 and p3:
                    self.model.add_line(p1, p3)

        # Render enemies
        for enemy_pos, _, _ in controller.enemies:
            corners = [
                [enemy_pos[0] - 20, 0, enemy_pos[1] - 20],
                [enemy_pos[0] + 20, 0, enemy_pos[1] - 20],
                [enemy_pos[0] + 20, 0, enemy_pos[1] + 20],
                [enemy_pos[0] - 20, 0, enemy_pos[1] + 20],
                [enemy_pos[0] - 20, 40, enemy_pos[1] - 20],
                [enemy_pos[0] + 20, 40, enemy_pos[1] - 20],
                [enemy_pos[0] + 20, 40, enemy_pos[1] + 20],
                [enemy_pos[0] - 20, 40, enemy_pos[1] + 20]
            ]
            projected = [self.project(p, controller.player_pos, controller.player_angle) for p in corners]
            if all(projected):
                edges = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
                for i, j in edges:
                    self.model.add_line(projected[i], projected[j])

        # Render lines with CRT effects
        for start, end in self.model.get_lines():
            intensity = self.model.glow_intensity + self.model.flicker
            intensity = max(0.5, min(1.0, intensity))
            color = (0, int(255 * intensity), 0)
            pygame.draw.line(self.screen, color, start, end, 2)

        # Render HUD
        text = self.font.render(f"Health: {controller.player_health}  Enemies: {len(controller.enemies)}", True, (50, 50, 50))
        self.screen.blit(text, (10, 10))
        pygame.display.flip()

    def project(self, point, player_pos, player_angle):
        # Simple perspective projection
        x, y, z = point
        px, pz = player_pos
        dx = x - px
        dz = z - pz
        # Rotate around Y-axis
        cos_a = math.cos(-player_angle)
        sin_a = math.sin(-player_angle)
        rx = dx * cos_a - dz * sin_a
        rz = dx * sin_a + dz * cos_a
        if rz < 10:  # Clip objects behind camera
            return None
        # Project to screen
        fov = 400
        screen_x = 400 + (rx * fov) / rz
        screen_y = 300 - (y * fov) / rz
        if 0 <= screen_x <= 800 and 0 <= screen_y <= 600:
            return (screen_x, screen_y)
        return None

# Controller: Handles user input and game logic
class VectorCRTController:
    def __init__(self, model, game):
        self.model = model
        self.game = game
        self.player_pos = [0, 0]  # [x, z]
        self.player_angle = 0.0
        self.player_speed = 100
        self.player_rotation_speed = 2.0
        self.projectiles = []  # (start, end, is_player)
        self.enemies = []  # (pos, angle, health)
        self.player_health = 100
        self.last_shot_time = 0
        self.shot_cooldown = 0.5
        self.enemy_spawn_timer = 0
        self.mouse_sensitivity = 0.005  # Added for mouse aiming
        pygame.mouse.set_visible(True)  # Visible in menu

    def handle_input(self, event, dt):
        if self.game.state == "menu":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.game.state = "game"
                pygame.mouse.set_visible(False)
                pygame.event.set_grab(True)  # Capture mouse in game
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                return False
            return True

        # Game state input
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                self.game.state = "menu"
                pygame.mouse.set_visible(True)
                pygame.event.set_grab(False)  # Release mouse in menu
                return False
        if event.type == pygame.MOUSEMOTION:
            print(f"Mouse motion: rel={event.rel}")  # Debug output
            self.player_angle -= event.rel[0] * self.mouse_sensitivity * dt
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            print(f"Mouse click at {event.pos}")  # Debug output
            current_time = pygame.time.get_ticks() / 1000
            if current_time - self.last_shot_time > self.shot_cooldown:
                self.last_shot_time = current_time
                start = [self.player_pos[0], self.player_pos[1]]
                end = [
                    self.player_pos[0] + math.sin(self.player_angle) * 1000,
                    self.player_pos[1] + math.cos(self.player_angle) * 1000
                ]
                self.projectiles.append((start, end, True))
                self.model.reset_glow()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.player_pos[0] += math.sin(self.player_angle) * self.player_speed * dt
            self.player_pos[1] += math.cos(self.player_angle) * self.player_speed * dt
        if keys[pygame.K_s]:
            self.player_pos[0] -= math.sin(self.player_angle) * self.player_speed * dt
            self.player_pos[1] -= math.cos(self.player_angle) * self.player_speed * dt
        if keys[pygame.K_a]:
            self.player_angle += self.player_rotation_speed * dt
        if keys[pygame.K_d]:
            self.player_angle -= self.player_rotation_speed * dt

        self.model.reset_glow()
        return True

    def update_enemies(self, dt, player_pos):
        self.enemy_spawn_timer += dt
        if self.enemy_spawn_timer > 5.0:
            self.enemy_spawn_timer = 0
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(500, 1000)
            enemy_pos = [
                player_pos[0] + math.sin(angle) * distance,
                player_pos[1] + math.cos(angle) * distance
            ]
            self.enemies.append((enemy_pos, 0.0, 1.0))

        for enemy in self.enemies[:]:
            e_pos, e_angle, e_health = enemy
            dx = player_pos[0] - e_pos[0]
            dz = player_pos[1] - e_pos[1]
            distance = math.sqrt(dx**2 + dz**2)
            if distance > 50:
                speed = 50
                e_pos[0] += (dx / distance) * speed * dt
                e_pos[1] += (dz / distance) * speed * dt
            if random.random() < 0.01:
                start = e_pos.copy()
                end = [
                    e_pos[0] + (dx / distance) * 1000,
                    e_pos[1] + (dz / distance) * 1000
                ]
                self.projectiles.append((start, end, False))
            enemy = (e_pos, e_angle, e_health)

    def handle_collisions(self):
        for proj in self.projectiles[:]:
            start, end, is_player = proj
            if is_player:
                for enemy in self.enemies[:]:
                    e_pos = enemy[0]
                    if math.hypot(e_pos[0] - start[0], e_pos[1] - start[1]) < 20:
                        self.enemies.remove(enemy)
                        self.projectiles.remove(proj)
                        break
            else:
                if math.hypot(self.player_pos[0] - start[0], self.player_pos[1] - start[1]) < 20:
                    self.player_health -= 10
                    self.projectiles.remove(proj)
                    if self.player_health <= 0:
                        self.game.state = "menu"
                        self.player_health = 100
                        self.enemies.clear()
                        self.projectiles.clear()
                        self.model.lines.clear()
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)

        for start, end, is_player in self.projectiles:
            p_start = self.game.view.project([start[0], 0, start[1]], self.player_pos, self.player_angle)
            p_end = self.game.view.project([end[0], 0, end[1]], self.player_pos, self.player_angle)
            if p_start and p_end:
                self.model.add_line(p_start, p_end)

# Main game class
class VectorCRTGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Battlezone: Vector CRT")
        pygame.event.set_grab(True)  # Capture mouse input
        self.clock = pygame.time.Clock()
        self.model = VectorCRTModel()
        self.view = VectorCRTView(self.model, self.screen)
        self.controller = VectorCRTController(self.model, self)
        self.state = "menu"
        self.running = True
        self.fps = 60

    async def main_loop(self):
        while self.running:
            dt = self.clock.tick(self.fps) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.running = self.controller.handle_input(event, dt)

            if self.state == "menu":
                self.view.render_menu()
            else:
                self.controller.update_enemies(dt, self.controller.player_pos)
                self.controller.handle_collisions()
                self.model.update_glow(dt)
                self.view.render_game(self.controller)

            await asyncio.sleep(1.0 / self.fps)

    def run(self):
        if platform.system() == "Emscripten":
            asyncio.ensure_future(self.main_loop())
        else:
            asyncio.run(self.main_loop())

    def __del__(self):
        pygame.quit()

# Entry point
if __name__ == "__main__":
    game = VectorCRTGame()
    game.run()