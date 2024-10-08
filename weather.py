# Author: Dani Alc
# Mail: danialcdev@gmail.com 
# Date: Aug 2024
# Description: Weather simulator using pygame
# This code can be used in any non-commerical project, and you may modify it as you want. 
# If you make any enhancements, please share them!  
# Also contact me for commercial applications


import pygame
import random
import math
pygame.mixer.init(frequency = 44100, size = -16, buffer = 2**12) 
pygame.mixer.set_num_channels(24)


class Weather:
    
    def __init__(self, screen: pygame.Surface, weather_types: list[str] = None, wind_speed: int = 30, pixel: bool = False):
        """
        Initialize the Weather system.

        :param screen: The Pygame screen where the weather effects will be drawn.
        :param weather_types: List of weather effects to initialize.
                              Supported types: 'rain', 'acid rain', 'snow', 'hail', 'lightning', 'fog'.
        :param wind_speed: Maximum wind speed between 0 and 100 ideally. Positive is right direction and negative is left. If it's exacly 0 there won't be any wind nor gusts.
        :param pixel: If True, snow and hail will be drawn as squares instead of circles.
        """
        self.screen = screen
        self.wind_speed = wind_speed
        self.pixel:bool = pixel
        self.effects:dict = {} # dict that contains all current weather conditions. The key is a string and ther value the class itself. 

        self.general_vol:float = 1.0  # From 0.0 to 1.0: Volume modificator for all sounds. 
        self.sounds: list = []        # Empty list to store all sounds before playing them
        self.channels: dict = {}      # Empty dict to store all the channels playing sounds and their initial volume 
        self.timer:int = 0            # Used to store time for the delay playing different sounds

        if weather_types is None:
            pass
        else:
            if wind_speed:
                self.wind = Wind(self, wind_speed, sound = True)  

            if 'rain' in weather_types:
                self.effects['rain'] = Rain(self, screen, width=10, height=150, initial_speed=15, acc=50,
                                            color=(150, 200, 255, 155), flake=False, num_drops=30)

            if 'acid rain' in weather_types:
                self.effects['acid rain'] = Rain(self, screen, width=10, height=150, initial_speed=15, acc=50,
                                                 color=(150, 255, 155, 155), flake=False, num_drops=30)

            if 'snow' in weather_types:
                self.effects['snow'] = Snow(self, screen, width=25, height=40, initial_speed=2, acc=1, color=(255, 255, 255, 255),
                                            flake=True, num_drops=40, pixel=self.pixel)

            if 'hail' in weather_types:
                self.effects['hail'] = Hail(self, screen, width=25, height=50, initial_speed=30, acc=20,
                                            color=(220, 220, 220, 220), flake=True, num_drops=30, pixel=self.pixel)

            if 'lightning' in weather_types:
                self.effects['lightning'] = Lightning(self, screen)

            if 'fog' in weather_types:
                self.effects['fog'] = Fog(screen, pixel=self.pixel)

        self.initial_sounds = self.sounds.copy()

    def update(self) -> None:
        """
        Update and render all active weather effects.
        """
        
        # Update wind and apply to other effects
        current_wind_speed = self.wind.update(self) if self.wind_speed else 0
        
        # Update each other weather effect
        upd_rects = []

        for effect_name in ['lightning', 'fog', 'snow', 'rain', 'acid rain', 'hail']:
            if effect_name in self.effects:
                updated_rect = self.effects[effect_name].update(current_wind_speed)
                if updated_rect is not None:
                    upd_rects.extend(updated_rect)

        pygame.display.update(upd_rects)  # Update only the rectangles that are changed
        
        #Play sounds
        if self.sounds:
            new_timer = (pygame.time.get_ticks()//656 + 1) % 20            
            if new_timer > self.timer:
                volume = 1.5/(len(self.initial_sounds))    
                
                self.timer = new_timer

                channel = pygame.mixer.find_channel() # Looks for an empty channel 
                channel.play(self.sounds[0], -1) # Plays sound on this channel in a loop
                
                channel.set_volume(volume*self.general_vol)  
                self.channels[channel] = volume

                self.sounds.pop(0) # Removes the sound from the list when it is already playing in loop 
                # print(f'sec:{new_timer} playing sound at {volume*self.general_vol*100 :.0f}% volume. {len(self.sounds)} left to play')
        

    def toggle_effect(self, effect_name: str) -> None:
        """Toggle the visibility of a specific weather effect."""
        if effect_name in self.effects:
            del self.effects[effect_name]
        else:
            self.__init__(self.screen, [effect_name] + list(self.effects.keys()))

    def set_wind_speed(self, base_max_speed, freq_base)-> None:
        """Manually set the wind speed."""
        self.wind.reset(self, base_max_speed, freq_base, self.wind.max_gusts, self.wind.freq_gusts)

    def set_fog_density(self, density: float, color: list[int, int, int] | None = None )-> None:
        """Set the density (and color if needed) of the fog effect."""
       
        if 'fog' in self.effects:
            if color == None: color = self.effects['fog'].color
            self.effects['fog'].load_images(density, color, self.pixel) 

    def set_lightning_frequency(self, frequency: int)-> None:
        """
        Set the frequency of lightning strikes. 

        :param frequency: Milliseconds between lightnings +/-20%
        """

        if 'lightning' in self.effects:
            self.effects['lightning'].frequency = frequency

    def change_volume(self, new_vol):
        '''
        Sets the volume of all the sounds simulated
        :param new_vol: float  # From 0.0 to 1.0. Being 0 completely silent and 1 the initial volume when the sound was created by the first time.
        '''

        if 0.0<= new_vol <= 1.0 :
            self.general_vol = new_vol 
            for channel, ini_vol in self.channels.items():
                channel.set_volume(ini_vol*new_vol)  
            
            if 'lightning' in self.effects.keys():
                self.effects['lightning'].gen_vol = new_vol

        else:
            raise ValueError

class Wind:
    """
    Class representing wind, which can affect the movement of precipitation.

    :param weather: Instance of the weather class
    :param base_max_speed: The maximum base wind speed. Ideally, from -100 to 100; the higher the absolute number, the higher the wind gets.
    :param amplitude: From 0 to 100, a 0 will mean that base speed is constant and 100 means that the wind oscillates between (negative) -base_max_speed and +base_max_speed
    :param freq_base: The frequency of the base wind speed variation. Ideally, from 0 to 100; more than 100 works but is too erratic.
    :param max_gusts: The maximum wind speed during gusts.
    :param freq_gusts: The frequency of the gusts. Ideally, from 0 to 100.
    :param sound: boolean. If is True, wind sounds will be generated.
    """

    def __init__(self, weather,  base_max_speed: int, amplitude: int = 55, freq_base: int = 50, max_gusts: int = 3, freq_gusts: int = 50, sound: bool = True):
        self.reset(weather, base_max_speed, amplitude, freq_base, max_gusts, freq_gusts, sound)
    
    def reset(self, weather, base_max_speed, amplitude, freq_base, max_gusts, freq_gusts, sound):
        self.base_max_speed: int = base_max_speed
        self.freq_base: int = freq_base 
        self.amplitude: int = amplitude
        self.max_gusts:int = max_gusts
        self.gusts = random.uniform(self.max_gusts / 2, self.max_gusts)
        self.freq_gusts: int = freq_gusts
        self.sound: bool = sound

        self.wind_sounds = []
        self.w_timer = 0 # Used to store time for the delay playing different wind sounds

        self.start_time = pygame.time.get_ticks()
        
        # Play sounds
        if sound: 
            for i in range(3):
                sound = pygame.mixer.Sound(f'assets/weather/wind/{i+1}.mp3')
                self.wind_sounds.append(sound) 
                pygame.mixer.find_channel().play(self.wind_sounds[i], -1)

        # Update speed at init
        self.update(weather)
            

    def update(self, weather) -> float:
        """
        Update the wind speed based on the current time and sinusoidal variations. Returns the speed value at this moment
        """
        t = (pygame.time.get_ticks() - self.start_time) / 1000  # Time in seconds

        # Generate a sinusoidal value for regular wind
        max_speed = self.base_max_speed 
        dif_speed =  (self.base_max_speed * self.amplitude) // 100 
        mean_speed = max_speed - dif_speed
 
        base_var = dif_speed*math.sin(2 * math.pi * self.freq_base/1000 * t)

        base_wind = mean_speed+base_var

        # Generate a series of sinusoidal gusts
        gusts_sum = 0
        for i in range(10):
            gusts_var = math.sin(2 * math.pi * (i+1) * self.freq_gusts/500 * t)
            gusts_sum += self.gusts * gusts_var

        # When gusts value is close to 0, a new base speed is established the gusts
        if -0.01 < gusts_var < 0.01:
            self.gusts = random.uniform(self.max_gusts // 2, self.max_gusts)

        # Add the base value and the gust to get the total speed
        self.speed = base_wind + gusts_sum

        #Set wind volume according to its speed
        if self.sound:
            for i in range(3):
                self.wind_sounds[i].set_volume(((abs(base_wind)-3)*0.0025*weather.general_vol))  

        return self.speed


class Precipitation:
    """
    Base class for precipitation effects such as rain, snow, or hail.

    The value of height, width, and initial_speed of the drops follow a linear sequence,
    ranging from 25% of each max value for the first drop to 100% for the last drop.

    :param weather: Instance of the weather class
    :param screen: The Pygame screen where the weather effects will be drawn.
    :param width: Max width of all drops.
    :param height: Max height of each drop.
    :param initial_speed: Max initial speed for each drop.
    :param acc: Max acceleration for each drop.
    :param color: A tuple representing the RGB+Alpha color of the drops.
    :param num_drops: The number of drops to generate. There will always be this quantity on the screen.
    :param flake: If True, a circle (or square, if pixel is True) will be drawn at the lower part of the sprite.
    :param pixel: If True, the flake will be drawn as a square instead of a circle.
    """

    def __init__(self, weather, screen: pygame.Surface, width: int, height: int, initial_speed: int, acc: int,
                 color: tuple[int, int, int, int], num_drops: int, flake: bool = False, pixel: bool = False, is_hail=False):
        self.screen = screen
        self.width = width
        self.height = height
        self.initial_speed = initial_speed
        self.acc = acc
        self.flake = flake
        self.is_hail = is_hail
        self.color = color
        self.pixel = pixel

        self.num_drops = num_drops
        self.drops = [] #List to store all the drops from the current class


    def create_drop(self, screen, initial_speed, acc, flake, is_hail):

        scale = 0.35 + 0.65 * random.random()
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
        else: new_drop = Precipitation.Drop(speed, acceleration, weight, pic, screen)
        
        self.drops.append(new_drop)

    def update(self, wind_speed: float = 0) -> list[pygame.Rect]:
        """
        Update and render all precipitation drops.

        :param wind_speed: The current speed of the wind affecting the precipitation.
        :return: A list of rectangles to be updated.
        """

        # Add or delete drops until there are the same as self.num_drops
        if len(self.drops) < self.num_drops:
            self.create_drop(self.screen, self.initial_speed, self.acc, self.flake, self.is_hail)
        elif len(self.drops) > self.num_drops:
            del self.drops[0]

        # Update the rectangles where the drops are now and where they were in the last loop.
        update_rects = []
        for drop in self.drops:
            r = drop.render(self.screen, wind_speed)
            if r:
                i = r.collidelist(update_rects)
                if i > -1:
                    update_rects[i].union_ip(r)
                else:
                    update_rects.append(r)
        return update_rects

    class Drop:
        """A single drop used by the precipitation generator."""
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
            self.current_speed_x = self.current_speed_x//2 + wind_speed//4
            self.pos = [random.random() * self.screen_w, - self.size[1]]

        def _reset_on_sides(self, left: bool) -> None:
            """Restart the drop on one side of the screen."""
            self.current_speed_y = self.ini_speed * random.uniform(1, 1.5)
            if left:   self.pos = [-self.size[0], random.random() * self.screen_h]
            else:      self.pos = [self.screen_w, random.random() * self.screen_h]

        def render(self, screen: pygame.Surface, wind_speed: float) -> pygame.Rect | None:
            """
            Updates the position/speed of the drop and then draws it on the screen.

            :param screen: The Pygame screen where the drop will be drawn.
            :param wind_speed: The current wind speed affecting the drop current_speed_x.
            :return: The rectangle area where the drop was drawn.
            """

            oldrect = self.pic.get_rect()

            rotated_pic = self.pic  # Initialize to the default picture

            if wind_speed:
                dx = (wind_speed - self.current_speed_x)*(1 - self.weight)**2
                
                self.current_speed_x += dx/1000
                if self.current_speed_x > 1: self.current_speed_x -= (self.current_speed_x**0.5) / 100 
                elif self.current_speed_x < -1: self.current_speed_x += ((abs(self.current_speed_x))**0.5) / 100
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

class Rain(Precipitation):
    def __init__(self, weather, screen, height=150, width=10, initial_speed=15, acc=5, color=(150, 200, 255, 200), flake=False, num_drops=25):
        super().__init__(weather, screen, height=height, width=width, initial_speed=initial_speed, acc=acc, color=color, flake=flake, num_drops=num_drops)

        for i in range(4):
            sound = pygame.mixer.Sound(f'assets/weather/rain/{i+1}.mp3')
            weather.sounds.append(sound) 

            

class Snow(Precipitation):
    """
    Class representing snow Precipitationitation.

    Snowflakes can be drawn as circles or squares, depending on the 'pixel' parameter.

    :param weather: Instance of the weather class
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

    def __init__(self, weather, screen: pygame.Surface, height: int = 50, width: int = 25, initial_speed: float = 2,
                 acc: float = 0.1, color: tuple[int, int, int, int] = (255, 255, 255, 255), flake: bool = True,
                 num_drops: int = 35, pixel: bool = False):
        super().__init__(weather=weather, screen=screen, height=height, width=width, initial_speed=initial_speed, acc=acc, color=color,
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


class Hail(Precipitation):
    """
    Class representing hail precipitation.

    Hail can bounce when it reaches the bottom of the screen, and can be drawn as circles or squares.

    :param weather: Instance of the weather class
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

    def __init__(self, weather, screen: pygame.Surface, width: int = 10, height: int = 50, initial_speed: float = 20,
                 acc: float = 1, color: tuple[int, int, int, int] = (200, 200, 200, 255), flake: bool = True,
                 num_drops: int = 10, pixel: bool = False, is_hail:bool=True):
        super().__init__(weather=weather, screen=screen, height=height, width=width, initial_speed=initial_speed, acc=acc, color=color,
                         flake=flake, num_drops=num_drops, pixel=pixel, is_hail=is_hail)
        for i in range(3):
            sound = pygame.mixer.Sound(f'assets/weather/hail/{i+1}.mp3')
            weather.sounds.append(sound)         

    class Drop(Precipitation.Drop):
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

        def render(self, screen: pygame.Surface, wind_speed: float) -> pygame.Rect | None:
            """
            Render the hailstone, allowing it to bounce when it hits the bottom of the screen.

            :param screen: The Pygame screen where the hailstone will be drawn.
            :param wind_speed: The current wind speed affecting the hailstone.
            :return: The rectangle area where the hailstone was drawn.
            """
            rect = super().render(screen, wind_speed)
            
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


class Lightning:
    """
    Class representing lightning effects.

    :param weather: Instance of the weather class
    :param screen: The Pygame screen where the lightning will be drawn.
    :param frequency: The frequency of lightning strikes, in milliseconds.
    """

    def __init__(self, weather, screen: pygame.Surface, frequency: int = 8_000):
        self.screen = screen
        self.frequency = frequency
        self.time_for_lightning = random.randint(self.frequency - self.frequency // 3, self.frequency + self.frequency // 3)

        self.surface = pygame.Surface(self.screen.get_size())
        self.surface.fill((255, 255, 255))
        
        self.last_flash_time = pygame.time.get_ticks()
        self.flash_active = False
        self.flash_step = 0
        self.step_duration = []

        self.general_vol = weather.general_vol
        self.th_sounds = []
        for i in range(5):
            sound = pygame.mixer.Sound(f'assets/weather/thunders/{i+1}.mp3')
            self.th_sounds.append(sound) 

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
        
        # print(self.step_duration, self.flash_step)

    def _start_flash(self) -> None:
        """Start a lightning flash event."""
        self.time_for_lightning = random.randint(self.frequency - self.frequency // 3, self.frequency + self.frequency // 3)
        self.flash_active = True
        self.flash_step = 0
        number_of_flashes = random.randint(1,3) #The number of flashes in this event.
        self.step_duration = [random.randint(200, 300) for _ in range(number_of_flashes * 2)]  # Create random durations for the flashes
        if number_of_flashes == 1: extra_duration_for_sounds = [random.randint(500, 1500)-sum(self.step_duration), 1, 1, 1, 1, 1] 
        else:                      extra_duration_for_sounds = [random.randint(500, 1500)-sum(self.step_duration), 1, 500, 1, 500, 1] 
        self.step_duration.extend(extra_duration_for_sounds) # Adds extra time at the end for playing the sounds
        self.flash_step_total = len(self.step_duration)

    def _continue_flash(self, current_time: int) -> None:
        """Continue a lightning flash event."""
        if self.flash_step < self.flash_step_total: 
            elapsed_time = current_time - self.last_flash_time

            #First blit the surface. It creates a flashing effect by changing the transparency (alpha) of the surface  
            if self.flash_step < self.flash_step_total-6: 
                if self.flash_step % 2 == 0:
                    alpha = 70*(elapsed_time/self.step_duration[self.flash_step])
                    self.surface.set_alpha(alpha)
                else:
                    alpha = 70*(self.step_duration[self.flash_step]/elapsed_time)
                    self.surface.set_alpha(alpha)
                self.screen.blit(self.surface, (0, 0))
            
            else: #on the last 6 steps of self.flash_step_total  
                if self.flash_step % 2 == 1:
                    chanel = pygame.mixer.find_channel()
                    chanel.set_volume(self.general_vol)
                    chanel.play(self.th_sounds[random.randint(0,len(self.th_sounds)-1)]) 
            
            #If the time on this step is over, it will jump to the next one 
            if elapsed_time >= self.step_duration[self.flash_step]:
                self.flash_step += 1
                self.last_flash_time = current_time

        # On the last step flash_active is swithed off
        elif self.flash_step >= self.flash_step_total: 
            self.flash_active = False


class Fog:
    """
    Class representing fog effects.

    :param screen: The Pygame screen where the fog will be drawn.
    :param color: The color of the fog in RGB.
    :param density: A value between 0 and 1 representing how dense the fog is.
    :param pixel: Bollean. If True, it will load a pixelated image.
    :param inertia: From 0 to 100. Being 0 means that the fog image almost follows wind speed, and 100 means that the wind barely affects the movement.
    """

    def __init__(self, screen: pygame.Surface, density: float = 0.7, pixel: bool=False, drag = 0, color: tuple[int, int, int] = (20, 0, 20), inertia: int = 10):
        self.screen = screen
        self.screen_w = screen.get_width()
        self.screen_h = screen.get_height()
        self.color = color
        self.inertia = inertia 
        self.speed = 0 # Displacement of the image in x direction
        self.y_ampl = random.random()*(self.screen_h // 4) # Amplitude of the sin function that controls the displacement of the image in y direction

        self.load_images(density, color, pixel)

    def load_images(self, density, color, pixel):
        # Load images
        if pixel: img = pygame.image.load(f'assets/weather/NoisePix.png').convert_alpha()  # Available at https://danialc0.itch.io/tileable-fog 
        else:     img = pygame.image.load(f'assets/weather/NoiseReg.png').convert_alpha() 
        img = pygame.transform.scale(img, (self.screen_w*1.5 - 1, self.screen_h * 2))
        img.set_alpha(int(255*density))
        
        color_surface = pygame.Surface(img.get_size())
        color_surface.fill(color)
        color_surface.set_alpha(100*density)
        img.blit(color_surface, (0, 0))
        
        self.img = []
        num_img = 2

        for _ in range(num_img):    
            self.img.append(img)

        # Position to start moving the fog from
        self.offset_1 = -self.screen_w*1.5
        self.offset_2 = 1

    def update(self, wind_speed: float) -> None:
        """
        Update the fog effect, moving it across the screen based on wind speed.

        :param wind_speed: The current wind speed affecting the fog.
        """
        dx = (wind_speed - self.speed)
        self.speed += dx/(10*self.inertia)

        # Move the fog across the screen in x direction
        self.offset_1 += self.speed
       
        # Move the fog across the screen in y direction
        y_movement = self.y_ampl * math.sin(pygame.time.get_ticks()/10_000)
        y_pos = -(self.screen_h // 4) + y_movement

        if -0.01 < y_pos < 0.01:
            self.y_ampl = random()*(self.screen_h // 4)

        if self.offset_1 > self.screen_w*1.5:
            self.offset_1 = -self.screen_w*1.5
        elif self.offset_1 < -self.screen_w*1.5:
            self.offset_1 = self.screen_w*1.5 

        self.offset_2 = self.offset_1 + self.screen_w*1.5 if self.offset_1 <= 0 else self.offset_1 - self.screen_w*1.5
        
        # Blit the fog surface onto the screen
        self.screen.blit(self.img[0], (self.offset_1, y_pos))
        self.screen.blit(self.img[1], (self.offset_2, y_pos))



def main():
    import time
    SCREENSIZE = 1200, 800
    PIXEL = True

    pygame.init()
    screen = pygame.display.set_mode(SCREENSIZE)
    clock = pygame.time.Clock()

    # Weather options: ['rain', 'acid rain', 'snow', 'hail', 'lightning', 'fog']
    weather = Weather(screen, weather_types=['rain', 'acid rain', 'snow', 'hail', 'lightning', 'fog'], pixel=PIXEL)
    bgrd = pygame.image.load(f'assets/weather/imgpix.webp').convert_alpha() if PIXEL else pygame.image.load(f'assets/weather/img.webp').convert_alpha() 
    bgrd = pygame.transform.scale(bgrd, (SCREENSIZE[0], SCREENSIZE[1]))


    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
        
        screen.blit(bgrd, (0,0))

        start_time = time.time()
        weather.update()
        
        # Other game logic here
        
        end_time = time.time()
        # print(f'Time for each frame: {end_time - start_time:.6f} seconds')
        
        pygame.display.flip()
        clock.tick(60)


if __name__ == '__main__':
    main()
