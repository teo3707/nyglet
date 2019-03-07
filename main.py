import pyglet.media
import pyglet
import ctypes


if __name__ == '__main__':
    driver = pyglet.media.get_audio_driver()
    listener = driver.get_listener()
    player = pyglet.media.Player()


    print(listener)
