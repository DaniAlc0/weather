import pygame
import random
import math


class Weather:
    def __init__(self, screen: pygame.Surface, weather_types: list[str] = None, wind_speed: int|float = 10, pixel: bool = False):
        """
        Initialize the Weather system.

        :param screen: The Pygame screen where the weather effects will be drawn.
        :param weather_types: List of weather effects to initialize.
                              Supported types: 'rain', 'snow', 'hail', 'lightning', 'fog'.
        :param wind_speed: Maximum wind speed. Positive is right direction and negative is left.
        :param pixel: If True, snow and hail will be drawn as squares instead of circles.
        """
        self.screen = screen
        self.pixel = pixel
        self.effects = {}

        if weather_types is None:
            pass
        else:
            self.wind = Wind(wind_speed, freq_base=0.02)  # Wind is always part of the system

            if 'rain' in weather_types:
                self.effects['rain'] = Rain(screen, width=10, height=150, initial_speed=15, acc=50,
                                            color=(150, 200, 255, 155), flake=False, num_drops=40)

            if 'acid rain' in weather_types:
                self.effects['acid rain'] = Rain(screen, width=10, height=150, initial_speed=15, acc=50,
                                                 color=(150, 255, 155, 155), flake=False, num_drops=40)

            if 'snow' in weather_types:
                self.effects['snow'] = Snow(screen, width=25, height=40, initial_speed=2, acc=1, color=(255, 255, 255, 255),
                                            flake=True, num_drops=40, pixel=self.pixel)

            if 'hail' in weather_types:
                self.effects['hail'] = Hail(screen, width=25, height=50, initial_speed=30, acc=20,
                                            color=(220, 220, 220, 220), flake=True, num_drops=40, pixel=self.pixel)

            if 'lightning' in weather_types:
                self.effects['lightning'] = Lightning(screen)

            if 'fog' in weather_types:
                self.effects['fog'] = Fog(screen, color=(200, 200, 200), density=0.5, pixel=self.pixel)

    def update(self) -> None:
        """
        Update and render all active weather effects.
        """
        self.screen.fill((0, 0, 0))  # Clear the screen before drawing weather effects

        # Update wind and apply to other effects
        self.wind.update()

        # Update each weather effect
        upd_rects = []

        if 'fog' in self.effects:
            self.effects['fog'].update(self.wind.speed)

        for effect_name in ['lightning', 'snow', 'rain', 'acid rain', 'hail']:
            if effect_name in self.effects:
                updated_rect = self.effects[effect_name].update(self.wind.speed)
                if updated_rect is not None:
                    upd_rects.extend(updated_rect)

        pygame.display.update(upd_rects)  # Update only the rectangles that are changed

    def toggle_effect(self, effect_name: str) -> None:
        """Toggle the visibility of a specific weather effect."""
        if effect_name in self.effects:
            del self.effects[effect_name]
        else:
            self.__init__(self.screen, [effect_name] + list(self.effects.keys()))

    def set_wind_speed(self, base_max_speed, freq_base)-> None:
        """Manually set the wind speed."""
        self.wind.reset(base_max_speed, freq_base, self.wind.max_gusts, self.wind.freq_gusts)

    def set_fog_density(self, density: float)-> None:
        """Set the density of the fog effect."""
        if 'fog' in self.effects:
            self.effects['fog'].density = density

    def set_lightning_frequency(self, frequency: int)-> None:
        """
        Set the frequency of lightning strikes. 

        :param frequency: Milliseconds between lightnings +/-20%
        """

        if 'lightning' in self.effects:
            self.effects['lightning'].frequency = frequency
            
class Precip:
    """
    Base class for precipitation effects such as rain, snow, or hail.

    The value of height, width, and initial_speed of the drops follow a linear sequence,
    ranging from 25% of each max value for the first drop to 100% for the last drop.

    :param screen: The Pygame screen where the weather effects will be drawn.
    :param width: Max width of all drops.
    :param height: Max height of each drop.
    :param initial_speed: Max initial speed for each drop.
    :param acc: Max acceleration for each drop.
    :param color: A tuple representing the RGBA color of the drops.
    :param num_drops: The number of drops to generate. There will always be this quantity on the screen.
    :param flake: If True, a circle (or square, if pixel is True) will be drawn at the lower part of the sprite.
    :param pixel: If True, the flake will be drawn as a square instead of a circle.
    """

    def __init__(self, screen: pygame.Surface, width: int, height: int, initial_speed: int, acc: int,
                 color: tuple[int, int, int, int], num_drops: int, flake: bool = False, pixel: bool = False, is_hail=False):
        self.screen = screen
        self.width = width
        self.height = height
        self.color = color
        self.pixel = pixel

        self.num_drops = num_drops
        self.create_drops(screen, initial_speed, acc, num_drops, flake, is_hail)

    def create_drops(self, screen, initial_speed, acc, num_drops, flake, is_hail):
        self.drops = []
        for drop in range(num_drops):
            scale = 0.35 + 0.65 * (num_drops - drop) / num_drops
            weight = scale*0.9
            w, h = int(scale * self.width), int(scale * self.height)
            speed = scale * initial_speed
            acceleration = scale * acc / 100  # The bigger the more it accelerates

            pic = pygame.Surface((w, h), pygame.SRCALPHA, 32).convert_alpha()
            r, g, b, a = self.color

            transparency_tail_x = [1 - abs((i - w // 2) / (w // 2)) for i in range(w)]
            transparency_tail_y = (a * scale) / h

            for j in range(h - w):
                for i in range(w):
                    alphax = transparency_tail_x[i] ** 2
                    alphay = transparency_tail_y * j
                    rect = (i, j, 1, 1)  # Pixel in position i,j
                    pic.fill((r, g, b, int(alphay * alphax)), rect)

            if flake:
                weight /= 2
                if self.pixel:
                    pygame.draw.rect(pic, (r, g, b, 255), (w // 4, h - w, w // 2, w // 2))
                else:
                    pygame.draw.circle(pic, (r, g, b, 255), (w // 2, h - w), w // 4)

            if is_hail: new_drop = Hail.Drop(speed, acceleration, weight, pic, screen)
            else: new_drop = Precip.Drop(speed, acceleration, weight, pic, screen)
            
            self.drops.append(new_drop)

    def update(self, wind_speed: float = 0) -> list[pygame.Rect]:
        """
        Update and render all precipitation drops.

        :param wind_speed: The current speed of the wind affecting the precipitation.
        :return: A list of dirty rectangles that were updated.
        """
        now = pygame.time.get_ticks() / 1000.0
        dirtyrects = []

        for drop in self.drops:
            r = drop.render(self.screen, now, wind_speed)
            if r:
                i = r.collidelist(dirtyrects)
                if i > -1:
                    dirtyrects[i].union_ip(r)
                else:
                    dirtyrects.append(r)

        return dirtyrects

    class Drop:
        """A single drop used by the precipitation generator."""

        nexttime = 0  # The next time the drop will draw
        interval = 0.01  # How frequently the drop should draw

        def __init__(self, speed: float, acc: float, weight: float, pic: pygame.Surface, screen: pygame.Surface):
            """
            Initialize a precipitation drop.

            :param speed: The initial speed of the drop.
            :param acc: The acceleration of the drop.
            :param pic: The Pygame surface representing the drop.
            :param: Weight of the drop from 0 to 1. The higher it is the less it's afected by the wind direction
            :param screen: The Pygame screen where the drop will be drawn.
            """
            self.pic = pic
            self.size = pic.get_size()

            self.ini_speed = speed
            self.acceleration = acc
            self.weight = weight

            self.screen_w = screen.get_width()
            self.screen_h = screen.get_height()

            self.pos = [random.random() * self.screen_w, -random.randint(-self.screen_h, self.screen_h)]
            self.current_speed_x = 0
            self.current_speed_y = self.ini_speed * random.uniform(1, 1.5)

        def _reset_on_top(self, wind_speed) -> None:
            """Restart the drop at the top of the screen."""
            self.current_speed_y = self.ini_speed * random.uniform(1, 1.5)
            self.current_speed_x = wind_speed//2
            self.pos = [random.random() * self.screen_w, - self.size[1]]

        def _reset_on_sides(self, left: bool) -> None:
            """Restart the drop on one side of the screen."""
            self.current_speed_y = self.ini_speed * random.uniform(1, 1.5)
            if left:
                self.pos = [-50, random.random() * self.screen_h]
            else:
                self.pos = [self.screen_w, random.random() * self.screen_h]

        def render(self, screen: pygame.Surface, now: float, wind_speed: float) -> pygame.Rect | None:
            """
            Draw the drop on the screen.

            :param screen: The Pygame screen where the drop will be drawn.
            :param now: The current time in seconds.
            :param wind_speed: The current wind speed affecting the drop current_speed_x.
            :return: The rectangle area where the drop was drawn.
            """
            if now < self.nexttime:
                return None

            self.nexttime = now + self.interval
            oldrect = self.pic.get_rect()

            rotated_pic = self.pic  # Initialize to the default picture

            if wind_speed:
                self.current_speed_x += (wind_speed - self.current_speed_x)*(1-self.weight)**5
                self.pos[0] += self.current_speed_x

                # Calculate tilt angle (in radians)
                tilt_angle = math.atan2(self.current_speed_x, self.current_speed_y)

                # Rotate the drop's pic surface
                rotated_pic = pygame.transform.rotate(self.pic, math.degrees(tilt_angle))

            if self.pos[0] < -51:
                self._reset_on_sides(left=False)
            if self.pos[0] > self.screen_w + 15:
                self._reset_on_sides(left=True)

            # Update the drop's position
            self.pos[1] += self.current_speed_y

            newrect = pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
            rect = oldrect.union(newrect)

            # Draw the rotated drop
            screen.blit(rotated_pic, self.pos)

            self.current_speed_y += self.acceleration

            if self.pos[1] > self.screen_h:
                self._reset_on_top(wind_speed)

            return rect

class Rain(Precip):
    def __init__(self, screen, height=150, width=10, initial_speed=15, acc=5, color=(150, 200, 255, 200), flake=False, num_drops=25):
        super().__init__(screen, height=height, width=width, initial_speed=initial_speed, acc=acc, color=color, flake=flake, num_drops=num_drops)

class Snow(Precip):
    """
    Class representing snow precipitation.

    Snowflakes can be drawn as circles or squares, depending on the 'pixel' parameter.

    :param screen: The Pygame screen where the snow will be drawn.
    :param height: Max height of the snowflakes.
    :param width: Max width of the snowflakes.
    :param initial_speed: Max initial speed for each snowflake.
    :param acc: Max acceleration for each snowflake.
    :param color: RGBA color of the snowflakes.
    :param flake: If True, snowflakes will be drawn at the lower part of the sprite.
    :param num_drops: The number of snowflakes to generate.
    :param pixel: If True, snowflakes will be drawn as squares instead of circles.
    """

    def __init__(self, screen: pygame.Surface, height: int = 50, width: int = 25, initial_speed: float = 2,
                 acc: float = 0.1, color: tuple[int, int, int, int] = (255, 255, 255, 255), flake: bool = True,
                 num_drops: int = 35, pixel: bool = False):
        super().__init__(screen, height=height, width=width, initial_speed=initial_speed, acc=acc, color=color,
                         flake=flake, num_drops=num_drops, pixel=pixel)

    def render(self, screen: pygame.Surface, now: float, wind_speed: float) -> pygame.Rect | None:
        """
        Render the snowflakes, taking into account the wind speed.

        :param screen: The Pygame screen where the snowflakes will be drawn.
        :param now: The current time in seconds.
        :param wind_speed: The current wind speed affecting the snowflakes.
        :return: The rectangle area where the snowflakes were drawn.
        """
        rect = super().render(screen, now, wind_speed * 4)
        return rect


class Hail(Precip):
    """
    Class representing hail precipitation.

    Hail can bounce when it reaches the bottom of the screen, and can be drawn as circles or squares.

    :param screen: The Pygame screen where the hail will be drawn.
    :param width: Max width of the hailstones.
    :param height: Max height of the hailstones.
    :param initial_speed: Max initial speed for each hailstone.
    :param acc: Max acceleration for each hailstone.
    :param color: RGBA color of the hailstones.
    :param flake: If True, hailstones will be drawn at the lower part of the sprite.
    :param num_drops: The number of hailstones to generate.
    :param pixel: If True, hailstones will be drawn as squares instead of circles.
    """

    def __init__(self, screen: pygame.Surface, width: int = 10, height: int = 50, initial_speed: float = 20,
                 acc: float = 1, color: tuple[int, int, int, int] = (200, 200, 200, 255), flake: bool = True,
                 num_drops: int = 10, pixel: bool = False, is_hail:bool=True):
        super().__init__(screen, height=height, width=width, initial_speed=initial_speed, acc=acc, color=color,
                         flake=flake, num_drops=num_drops, pixel=pixel, is_hail=is_hail)
        

    class Drop(Precip.Drop):
        """A single hailstone drop, with the ability to bounce."""

        def __init__(self, speed: float, acc: float, weight:float, pic: pygame.Surface, screen: pygame.Surface):
            """
            Initialize a hailstone drop.

            :param speed: The initial speed of the hailstone.
            :param acc: The acceleration of the hailstone.
            :param pic: The Pygame surface representing the hailstone.
            :param screen: The Pygame screen where the hailstone will be drawn.
            """
            super().__init__(speed, acc, weight, pic, screen)
            self.bounce_count = 0  # Track the number of bounces

        def render(self, screen: pygame.Surface, now: float, wind_speed: float) -> pygame.Rect | None:
            """
            Render the hailstone, allowing it to bounce when it hits the bottom of the screen.

            :param screen: The Pygame screen where the hailstone will be drawn.
            :param now: The current time in seconds.
            :param wind_speed: The current wind speed affecting the hailstone.
            :return: The rectangle area where the hailstone was drawn.
            """
            rect = super().render(screen, now, wind_speed)
            
            if self.pos[1] >= (self.screen_h - 20*(1-self.weight)):
                if self.bounce_count < 5:  # Limit the number of bounces
                    self.current_speed_y = -self.current_speed_y * 0.1 # Lose speed on bounce
                    self.current_speed_x += random.randint(-5,5)
                    self.bounce_count += 1
                else:
                    self._reset_on_top(wind_speed)
                    self.current_speed_x += random.randint(-5,5)
                    self.bounce_count = 0

            return rect


class Wind:
    """
    Class representing wind, which can affect the movement of precipitation.

    :param base_max_speed: The maximum base wind speed.
    :param freq_base: The frequency of the base wind speed variation.
    :param max_gusts: The maximum wind speed during gusts.
    :param freq_gusts: The frequency of the gusts.
    """

    def __init__(self, base_max_speed: float, freq_base: float = 0.05, max_gusts: float = 1, freq_gusts: float = 0.5):
        self.reset(base_max_speed, freq_base, max_gusts, freq_gusts)
    
    def reset(self, base_max_speed, freq_base, max_gusts, freq_gusts):
        self.base_max_speed = base_max_speed
        self.base_speed = random.uniform(base_max_speed // 2, base_max_speed)
        self.freq_base = freq_base

        self.max_gusts = max_gusts
        self.gusts = random.uniform(max_gusts // 2, max_gusts)
        self.freq_gusts = freq_gusts

        self.start_time = pygame.time.get_ticks()
        self.update()

    def update(self) -> None:
        """
        Update the wind speed based on the current time and sinusoidal variations.
        """
        t = (pygame.time.get_ticks() - self.start_time) / 1000  # Time in seconds

        # Generate a sinusoidal value for regular wind
        base_var = math.sin(2 * math.pi * self.freq_base * t)
        base_wind = self.base_speed * (0.2 + 0.8 * base_var)

        # Generate a sinusoidal value with random gusts
        gusts_var = math.sin(2 * math.pi * self.freq_gusts * t)
        gusts = self.gusts * gusts_var

        # When base value is close to 0, a new base speed is established
        if -0.01 < base_var < 0.01:
            self.base_speed = random.uniform(self.base_max_speed // 2, self.base_max_speed)
        if -0.01 < gusts_var < 0.01:
            self.gusts = random.uniform(self.max_gusts // 2, self.max_gusts)

        # Add the base value and the gust to get the total speed
        self.speed = base_wind + gusts


class Lightning:
    """
    Class representing lightning effects.

    :param screen: The Pygame screen where the lightning will be drawn.
    :param frequency: The frequency of lightning strikes, in milliseconds.
    :param flashes_per_thunder: The number of flashes in a single lightning event.
    """

    def __init__(self, screen: pygame.Surface, frequency: int = 5000, flashes_per_thunder: int = 3):
        self.screen = screen
        self.frequency = frequency
        self.time_for_lightning = random.randint(self.frequency - self.frequency // 5, self.frequency + self.frequency // 5)
        self.flashes_per_thunder = flashes_per_thunder

        self.surface = pygame.Surface(self.screen.get_size())
        self.last_flash_time = pygame.time.get_ticks()
        self.flash_active = False
        self.flash_step = 0
        self.flash_duration = []

    def update(self, wind_sp) -> None:
        """
        Update the lightning effect, checking if a flash should start or continue.
        """
        current_time = pygame.time.get_ticks()
        time_since_last_flash = current_time - self.last_flash_time

        if self.flash_active:  # Continue the flash if it is active
            self._continue_flash(current_time)
        elif time_since_last_flash > self.time_for_lightning:  # Checks if a flash should start
            self._start_flash()

    def _start_flash(self) -> None:
        """Start a lightning flash event."""
        self.time_for_lightning = random.randint(self.frequency - self.frequency // 5, self.frequency + self.frequency // 5)
        self.flash_active = True
        self.flash_step = 0
        self.flash_duration = [random.randint(100, 200) for _ in range(self.flashes_per_thunder * 2)]  # Create random durations for the flashes

    def _continue_flash(self, current_time: int) -> None:
        """Continue a lightning flash event."""
        if self.flash_step < (self.flashes_per_thunder * 2):
            elapsed_time = current_time - self.last_flash_time
            if self.flash_step % 2 == 0:
                self.surface.set_alpha(200)
                self.surface.fill((255, 255, 255))
            else:
                self.surface.set_alpha(30)

            self.screen.blit(self.surface, (0, 0))

            if elapsed_time >= self.flash_duration[self.flash_step]:
                self.flash_step += 1
                self.last_flash_time = current_time
        else:
            self.flash_active = False


class Fog:
    """
    Class representing fog effects.

    :param screen: The Pygame screen where the fog will be drawn.
    :param color: The color of the fog.
    :param density: A value between 0 and 1 representing how dense the fog is.
    :param pixel: If True, It will load a pixelated image.
    """

    def __init__(self, screen: pygame.Surface, color: tuple[int, int, int] = (200, 200, 200), density: float = 0.5, pixel: bool=False):
        self.screen = screen
        self.screen_w = screen.get_width()
        self.screen_h = screen.get_height()
        self.color = color
        self.density = density  # A value between 0 and 1 representing how dense the fog is
        self.pixel = pixel

        # Load images
        self.img = []
        num_img = 2
        for _ in range(num_img):
            if pixel: img = pygame.image.load(f'assets/NoisePix.png').convert_alpha()  # Available at https://danialc0.itch.io/tileable-fog 
            else:     img = pygame.image.load(f'assets/NoiseReg.png').convert_alpha() 
            img = pygame.transform.scale(img, (self.screen_w - 1, self.screen_h * 1.2))
            img.set_alpha(int(255*density))
            self.img.append(img)

        # Position to start moving the fog from
        self.offset_1 = -self.screen_w
        self.offset_2 = 1

    def update(self, wind_speed: float) -> None:
        """
        Update the fog effect, moving it across the screen based on wind speed.

        :param wind_speed: The current wind speed affecting the fog.
        """
        # Move the fog across the screen
        self.offset_1 += wind_speed

        y_movement = (self.screen_h // 15) * math.sin(math.pi * self.offset_1 / self.screen_w)
        y_pos = -(self.screen_h // 15) + y_movement

        if self.offset_1 > self.screen_w:
            self.offset_1 = -self.screen_w
        elif self.offset_1 < -self.screen_w:
            self.offset_1 = self.screen_w

        self.offset_2 = self.offset_1 + self.screen_w if self.offset_1 <= 0 else self.offset_1 - self.screen_w

        # Blit the fog surface onto the screen
        self.screen.blit(self.img[0], (self.offset_1, y_pos))
        self.screen.blit(self.img[1], (self.offset_2, y_pos))



def main():
    import time
    SCREENSIZE = 1200, 800

    pygame.init()
    screen = pygame.display.set_mode(SCREENSIZE)
    clock = pygame.time.Clock()

    # Weather options: ['rain', 'snow', 'hail', 'lightning', 'fog']
    weather = Weather(screen, weather_types=['rain', 'snow', 'hail', 'lightning', 'fog'], pixel=False)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        start_time = time.time()
        screen.fill((0, 0, 0))
        weather.update()
        
        # Other game logic here
        
        end_time = time.time()
        # print(f'Time for each frame: {end_time - start_time:.6f} seconds')
        
        pygame.display.flip()
        clock.tick(60)


if __name__ == '__main__':
    main()
