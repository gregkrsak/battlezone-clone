import unittest
from unittest.mock import patch
import pygame
from vector_crt_battlezone import VectorCRTModel, VectorCRTController, VectorCRTGame

class TestBattlezoneGame(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.model = VectorCRTModel()
        self.game = VectorCRTGame()
        self.controller = VectorCRTController(self.model, self.game)

    def tearDown(self):
        pygame.quit()

    def test_player_movement(self):
        initial_pos = self.controller.player_pos.copy()
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_w)
        with patch('pygame.time.get_ticks', return_value=1000):
            self.controller.handle_input(event, 0.1)
        self.assertNotEqual(self.controller.player_pos, initial_pos, "Player should move forward with W key")

    def test_shooting(self):
        initial_lines = len(self.model.lines)
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(400, 300))
        with patch('pygame.time.get_ticks', return_value=1000):
            self.controller.handle_input(event, 0.1)
        self.assertGreater(len(self.model.lines), initial_lines, "Shooting should add projectile lines")

    def test_enemy_movement(self):
        self.controller.enemies = [([100, 100], 0.0, 1.0)]
        initial_pos = self.controller.enemies[0][0].copy()
        self.controller.update_enemies(0.1, [0, 0])
        new_pos = self.controller.enemies[0][0]
        self.assertNotEqual(new_pos, initial_pos, "Enemy should move toward player")

    def test_collision_detection(self):
        self.controller.projectiles = [([10, 10], [20, 20], True)]
        self.controller.enemies = [([15, 15], 0.0, 1.0)]
        self.controller.handle_collisions()
        self.assertEqual(len(self.controller.enemies), 0, "Projectile should destroy enemy on collision")

    def test_menu_to_game_transition(self):
        self.game.state = "menu"
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
        self.controller.handle_input(event, 0.1)
        self.assertEqual(self.game.state, "game", "Space key should transition from menu to game")

    def test_mouse_input(self):
        initial_angle = self.controller.player_angle
        event = pygame.event.Event(pygame.MOUSEMOTION, rel=(10, 0))
        self.controller.handle_input(event, 0.1)
        self.assertNotEqual(self.controller.player_angle, initial_angle, "Mouse motion should update player angle")

if __name__ == '__main__':
    unittest.main()
    