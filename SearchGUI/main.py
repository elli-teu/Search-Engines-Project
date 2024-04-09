#!/usr/bin/env python3
from Scenes import main_scene
import game_engine
from game_engine import environment
from constants import FPS
import file_operations as file_op
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("A search engines for podcasts")
    file_op.load_all_images()
    game_engine.schedule_scene_change(main_scene.MainScene())
    running = True
    while running:
        running = environment.handle_events()
        game_engine.start_tick()
        game_engine.process_current_scene()

        environment.draw_screen()

        game_engine.end_tick()

        environment.clock.tick(FPS)
    pygame.quit()
