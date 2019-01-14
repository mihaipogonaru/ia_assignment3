from sim.medium import Medium

from typing import Tuple
import time

import sys, pygame

def main_loop(screen: pygame.Surface, medium: Medium, sq: Tuple[int, int], cycle_duration: float):
    white = (255, 255, 255)
    black = (0, 0, 0)
    green = (0, 255, 0)
    blue = (0, 0, 255)
    red = (255, 0, 0)

    sq_h, sq_l = sq
    medium_h, medium_l = medium.map_size
    font = pygame.font.SysFont('Arial', 10)

    max_population = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                break

        screen.fill(black)

        for x in range(medium_h):
            for y in range(medium_l):
                entities = medium.numberOfEntities(x, y)
                left, top = y * sq_l, x * sq_h

                rect = pygame.Rect(left, top, sq_l, sq_h)

                if medium.isWater(x, y):
                    pygame.draw.rect(screen, blue, rect)
                elif medium.isFood(x, y):
                    pygame.draw.rect(screen, green, rect)
                    screen.blit(font.render(str(medium.map[x][y].prop['resource']), True, red), (left, top + sq_h / 2))
                elif entities > 0:
                    pygame.draw.rect(screen, black, rect)
                else:
                    pygame.draw.rect(screen, white, rect)

                if entities > 0:
                    screen.blit(font.render(str(entities), True, red), (left, top))

        pygame.display.update()

        medium.update()

        print(f'Population {len(medium.entities)}')
        max_population = max(max_population, len(medium.entities))

        if not len(medium.entities):
            break

        time.sleep(cycle_duration)

    print(f'Max population {max_population}')


def init_pygame(screen_size) -> pygame.display:
    pygame.init()

    display = pygame.display.set_mode(screen_size)
    pygame.display.set_caption('LifeSim')

    return display

def main():
    if len(sys.argv) != 3:
        print(f'Usage: ./{sys.argv[0]} [input_file] [cycle_durantion_seconds]')
        sys.exit(-1)

    cycle_duration = float(sys.argv[2])

    medium = Medium(sys.argv[1])
    medium_h, medium_l = medium.map_size

    # square size
    sq = (30, 30)
    sq_h, sq_l = sq

    screen_size = (medium_l * sq_l, medium_h * sq_h)
    screen = init_pygame(screen_size)

    main_loop(screen, medium, sq, cycle_duration)

if __name__ == '__main__':
    main()
