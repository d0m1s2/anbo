import pygame
import time

pygame.mixer.init()
sound = pygame.mixer.Sound("your_sound_file.wav")
sound.play()
time.sleep(3)
