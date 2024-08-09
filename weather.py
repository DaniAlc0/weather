import pygame
import random
import math


class Weather:
    def __init__(self, screen, weather_types: list[str]=None):
        """
        Initialize the Weather system.

        :param screen: The Pygame screen where the weather effects will be drawn.
        :param weather_types: List of weather effects to initialize.
                              Supported types: 'rain', 'snow', 'hail', 'lightning', 'fog'
        """
        
        self.screen = screen
        self.effects = {}

        if weather_types is None:
            pass
        
        else:
            
            self.wind = Wind(base_max_speed=10, freq_base=0.02)  # Wind is always part of the system
            
            if 'rain' in weather_types:
                self.effects['rain'] = Rain(screen, width=10, height=150, initial_speed=15, acc=50, color=(150, 200, 255, 155), flake=False, num_drops=20)
                
            if 'snow' in weather_types:
                self.effects['snow'] = Snow(screen, width=25, initial_speed=2, acc=1, color=(255, 255, 255, 255), flake=True, num_drops=40)

            if 'hail' in weather_types:
                self.effects['hail'] = Hail(screen, width=25, height=50, initial_speed=30, acc=20, color=(220, 220, 220, 220), flake=True, num_drops=10)

            if 'lightning' in weather_types:
                self.effects['lightning'] = Lightning(screen)

            if 'fog' in weather_types:
                self.effects['fog'] = Fog(screen, color=(200, 200, 200), density=0.1)
        
    def update(self) -> None:
        """Update and render all active weather effects."""
        self.screen.fill((0, 0, 0))  # Clear the screen before drawing weather effects

        # Update wind and apply to other effects
        self.wind.update()
        
        # Update each weather effect
        upd_rects = []
        
        if 'lightning' in self.effects:
            self.effects['lightning'].update()
               
        if 'snow' in self.effects:
            upd_rects.extend(self.effects['snow'].update(self.wind.speed))
        
        if 'rain' in self.effects:
            upd_rects.extend(self.effects['rain'].update(self.wind.speed))
        
        if 'hail' in self.effects:
            upd_rects.extend(self.effects['hail'].update(self.wind.speed))

        if 'fog' in self.effects:
            self.effects['fog'].update(self.wind.speed)
        
        pygame.display.update(upd_rects)  # Update only the rectangles that are changed

    def toggle_effect(self, effect_name: str) -> None:
        """Toggle the visibility of a specific weather effect."""
        if effect_name in self.effects:
            del self.effects[effect_name]
        else:
            self.__init__(self.screen, [effect_name] + list(self.effects.keys()))

    def set_wind_speed(self, speed: float)-> None:
        """Manually set the wind speed."""
        self.wind.speed = speed

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

class Precip(object):
    """
    Initialize a Precip class such as rain, snow or hail. 
    The value of height, width and initial_speed of the drops follow a linear sequence, ranging from 25% of each max value for the first drop to a 100% for the last drop.

        :param screen: The Pygame screen where the weather effects will be drawn.
        :param width: Max width of all drops.  
        :param heigh: Max heigh of each drop.
        :param initial_speed: Max initial speed for each drop. 
        :param acc: Max acceleration for each drop.
        :param color: In R+G+B+Alpha
        :param num_drops: Quantity of drops generated. There will alway be this quantity on the screen.
        :param flake: Boolean. If true a circle will be drawn at the lower part of the sprite
    """

    def __init__(self, screen, width:int, height:int, initial_speed:int, acc:int, color:set[int, int, int, int], num_drops: int, flake:bool=False):
        self.screen = screen
        self.width = width
        self.height = height
        self.color = color

        self.num_drops = num_drops
        
        self.drops = []
        for drop in range(num_drops):
            scale = 0.25 + 0.75 * (num_drops - drop) / num_drops
            w, h = int(scale * self.width), int(scale * self.height)
            speed = scale * initial_speed
            acceleration = scale * acc / 100  #The bigger the more it accelerates

            pic = pygame.Surface((w, h), pygame.SRCALPHA, 32).convert_alpha()
            r, g, b, a = self.color

            transparency_tail_x = [1 - abs((i - w // 2) / (w // 2)) for i in range(w)]
            transparency_tail_y = (a * scale) / h

            for j in range(h-w):
                for i in range(w):
                    alphax = transparency_tail_x[i] ** 2
                    alphay = transparency_tail_y * j
                    rect = (i, j, 1, 1) # Pixel in position i,j
                    pic.fill((r, g, b, int(alphay * alphax)), rect)
            
            if flake: pygame.draw.circle(pic, (r, g, b, 255), (w//2, h-w), w//4)

            new_drop = Precip.Drop(speed, acceleration, pic, screen)
            self.drops.append(new_drop)

    def update(self, wind_speed=0):
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

    class Drop(object):
        """Drop used by precipitation generator"""
        nexttime = 0   # The next time the raindrop will draw
        interval = .01 # How frequently the raindrop should draw

        def __init__(self, speed, acc, pic, screen):
            self.pic = pic
            self.size = pic.get_size()
            
            self.ini_speed = speed
            self.acceleration = acc 

            self.screen_w = screen.get_width()
            self.screen_h = screen.get_height()

            self.pos = [random.random() * self.screen_w, -random.randint(-self.screen_h, self.screen_h)]
            self.current_speed = self.ini_speed * random.uniform(1, 1.5)

        def _reset_on_top(self):
            """Restart the drop at the top of the screen."""
            self.current_speed = self.ini_speed * random.uniform(1, 1.5)
            self.pos = [random.random() * self.screen_w, - self.size[1]]
            

        def _reset_on_sides(self, left:bool):
            """Restart the drop one one side of the screen."""
            self.current_speed = self.ini_speed * random.uniform(1, 1.5)
            if left: self.pos = [-50, random.random() * self.screen_h]
            else: self.pos = [self.screen_w, random.random() * self.screen_h]

        def render(self, screen, now, wind_speed):
            """ Draw the rain drop"""
            if now < self.nexttime:
                return None

            self.nexttime = now + self.interval
            oldrect = self.pic.get_rect()

            rotated_pic = self.pic  # Initialize to the default picture

            if wind_speed:
                self.pos[0] += wind_speed

                # Calculate tilt angle (in radians)
                tilt_angle = math.atan2(wind_speed, self.current_speed) 

                # Rotate the raindrop's pic surface
                rotated_pic = pygame.transform.rotate(self.pic, math.degrees(tilt_angle))

            if self.pos[0] < -51:  self._reset_on_sides(left=False)
            if self.pos[0] > self.screen_w+15:  self._reset_on_sides(left=True)

            # Update the raindrop's position
            self.pos[1] += self.current_speed

            newrect = pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
            rect = oldrect.union(newrect)

            # Draw the rotated raindrop
            screen.blit(rotated_pic, self.pos)

            self.current_speed += self.acceleration

            if self.pos[1] > self.screen_h:   self._reset_on_top()

            return rect

class Rain(Precip):
    def __init__(self, screen, height=150, width=10, initial_speed=15, acc=5, color=(150, 200, 255, 200), flake=False, num_drops=25):
        super().__init__(screen, height=height, width=width, initial_speed=initial_speed, acc=acc, color=color, flake=flake, num_drops=num_drops)

class Snow(Precip):
    def __init__(self, screen, height=50, width=25, initial_speed=2, acc=0.1, color=(255, 255, 255, 255), flake=True, num_drops=35):
        super().__init__(screen, height=height, width=width, initial_speed=initial_speed, acc=acc, color=color, flake=flake, num_drops=num_drops)
    def render(self, screen, now, wind_speed):
        rect = super().render(screen, now, wind_speed*4)
        return rect

class Hail(Precip):
    """ Added a bounce when it reches the bottom of the screen"""
    def __init__(self, screen, width=10, height=50, initial_speed=20, acc=1, color=(200, 200, 200, 255), flake=True, num_drops=10):
        super().__init__(screen, height=height, width=width, initial_speed=initial_speed, acc=acc, color=color, flake=flake, num_drops=num_drops)

    class Drop(Precip.Drop):
        def __init__(self, speed, acc, pic):
            super().__init__(speed, acc, pic)
            self.bounce_count = 0  # Track the number of bounces

        def render(self, screen, now, wind_speed):
            rect = super().render(screen, now, wind_speed)
            
            print("bounce")

            if self.pos[1] >= (self.screen_h- 100 - self.size[1]):
                if self.bounce_count < 3:  # Limit the number of bounces
                    self.current_speed = -self.current_speed * 0.6  # Lose some speed on bounce
                    self.bounce_count += 1
                    
                else:
                    self._reset_on_top()
                    self.bounce_count = 0
            return rect

class Wind:
    def __init__(self, base_max_speed: int|float, freq_base:float = 0.05, max_gusts: int|float=0.5, freq_gusts: float = 0.5):
      
        self.base_max_speed = base_max_speed 
        self.base_speed = random.uniform(base_max_speed//2, base_max_speed)
        self.freq_base = freq_base

        self.max_gusts = max_gusts
        self.gusts = random.uniform(max_gusts//2, max_gusts)
        self.freq_gusts = freq_gusts

        self.start_time = pygame.time.get_ticks()
        self.update()
        

    def update(self):
        t = (pygame.time.get_ticks()-self.start_time)/1000 #Time in seconds
        
        # Generate a sinusoidal value for regular wind
        base_var = math.sin(2 * math.pi * self.freq_base * t)
        base_wind = self.base_speed * (0.2 + 0.8*base_var)      

        # Generate a sinusoidal value with random gusts
        gusts_var = math.sin(2 * math.pi * self.freq_gusts * t)
        gusts = self.gusts * gusts_var
            

        # When base value is close to 0, a new base speed is stablished
        if -0.01 < base_var < 0.01:  self.base_speed = random.uniform(self.base_max_speed//2, self.base_max_speed)
        if -0.01 < gusts_var < 0.01:      self.gusts = random.uniform(self.max_gusts//2, self.max_gusts)
        
        # Add the base value and the gust to get the total speed
        self.speed = base_wind + gusts


class Lightning:
    def __init__(self, screen, frequency=5_000, flashes_per_thunder=3):
        self.screen = screen
        self.frequency = frequency
        self.time_for_lightning = random.randint(self.frequency -self.frequency //5, self.frequency +self.frequency //5)
        self.flashes_per_thunder = flashes_per_thunder

        self.surface = pygame.Surface((self.screen.get_size()))
        self.last_flash_time = pygame.time.get_ticks()
        self.flash_active = False
        self.flash_step = 0
        self.flash_duration = []


    def update(self):
        current_time = pygame.time.get_ticks()
        time_since_last_flash = current_time - self.last_flash_time

        if self.flash_active:        # Continue the flash if it is active
            self._continue_flash(current_time)

        elif time_since_last_flash > self.time_for_lightning: # Checks if a flash should start
            self._start_flash()
            
            
    def _start_flash(self):
        self.time_for_lightning = random.randint(self.frequency -self.frequency //5, self.frequency +self.frequency //5)
        self.flash_active = True
        self.flash_step = 0
        self.flash_duration = [random.randint(100, 200) for _ in range(self.flashes_per_thunder*2)] # Create random durations for the flashes 
        

    def _continue_flash(self, current_time):
        if self.flash_step < (self.flashes_per_thunder*2):
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
    def __init__(self, screen, color=(200, 200, 200), density=0.1):
        self.screen = screen
        self.screen_w = screen.get_width()
        self.screen_h = screen.get_height()
        self.color = color
        self.density = density  # A value between 0 and 1 representing how dense the fog is
        
        #Load images
        self.img = []
        num_img = 2
        for n in range(num_img):
            img = pygame.image.load(f'assets/images/Noise4.png').convert_alpha() # Used https://starshinescribbles.itch.io/fogandnoise pack
            img= pygame.transform.scale(img, (self.screen_w-1, self.screen_h*1.2))
            img.set_alpha(255)
            self.img.append(img)
      
        # Position to start moving the fog from
        self.offset_1 = - self.screen_w
        self.offset_2 = 1


    def update(self, wind_speed):
        # Move the fog across the screen
        self.offset_1 += wind_speed

        y_movement = (self.screen_h//15) * math.sin(math.pi * self.offset_1/self.screen_w)
        y_pos = -(self.screen_h//15) + y_movement

        if   self.offset_1 >  self.screen_w: self.offset_1 = -self.screen_w
        elif self.offset_1 < -self.screen_w: self.offset_1 = self.screen_w

        self.offset_2 = self.offset_1 + self.screen_w if self.offset_1 <= 0 else  self.offset_1 - self.screen_w 
        
        print(self.offset_1, self.offset_2, self.offset_1-self.offset_2)

        # Blit the fog surface onto the screen
        self.screen.blit(self.img[0], (self.offset_1, y_pos))
        self.screen.blit(self.img[1], (self.offset_2, y_pos))



def main():
    import time
    SCREENSIZE = 1200, 800

    pygame.init()
    screen = pygame.display.set_mode(SCREENSIZE)
    clock = pygame.time.Clock()

    #weather options: ['rain', 'snow', 'hail', 'lightning', 'fog']
    weather = Weather(screen, weather_types=['rain', 'snow', 'hail', 'lightning', 'fog'])

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        start_time = time.time()
        screen.fill((0, 0, 0))
        weather.update()
        print(f'{weather.wind.speed =}')

        
        # Other game logic here
        
        end_time = time.time()
        # print(f'Time for each frame: {end_time - start_time:.6f} seconds')
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == '__main__':
    main()
