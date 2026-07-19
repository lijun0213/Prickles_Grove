import pygame

currentMusic = None

def playMusic(path, volume=0.3):

    global currentMusic

    if currentMusic == path:
        return

    pygame.mixer.music.load(path)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(-1)

    currentMusic = path


def stopMusic():

    global currentMusic

    pygame.mixer.music.stop()
    currentMusic = None