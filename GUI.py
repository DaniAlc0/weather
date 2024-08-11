'''
WEATHER SIMULATOR

Select the desired conditions on the menu screen and click on "Start Simulation" or press Enter Key. 
During the simulation you can return to the menu by pressing any button on the keybord.
'''

import pygame
from weather import Weather

def main():

    class Button:
        """
        A simple button class for the GUI.

        :param text: The text to display on the button.
        :param position: The position of the button as a tuple (x, y).
        :param size: The size of the button as a tuple (width, height).
        :param colors: A tuple containing two colors (default, hovered).
        """
        def __init__(self, text: str, position: tuple[int, int], size: tuple[int, int], state = False,
                    colors: tuple[tuple[int, int, int], tuple[int, int, int]] = ((100, 100, 100), (150, 150, 150))):
            self.text = text
            self.position = position
            self.size = size
            self.colors = colors
            self.orig_colors  = colors
            self.rect = pygame.Rect(position, size)
            self.color = colors[0]
            self.font = pygame.font.Font(None, 36)
            self.state = state

        def draw(self, screen: pygame.Surface) -> None:
            """Draw the button on the screen."""
            pygame.draw.rect(screen, self.color, self.rect)
            text_surf = self.font.render(self.text, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=self.rect.center)
            screen.blit(text_surf, text_rect)

        def check_hover(self, mouse_pos: tuple[int, int]) -> None:
            """Change the button color if hovered."""
            if self.rect.collidepoint(mouse_pos):
                self.color = self.colors[1]
            else:
                self.color = self.colors[0]

        def is_clicked(self, mouse_pos: tuple[int, int]) -> bool:
            """Check if the button is clicked."""
            return self.rect.collidepoint(mouse_pos)

        def toggle(self) -> None:
            """Toggle the state of the button and update its color."""
            self.state = not self.state
            self.colors = ((0, 120, 0),(0, 190, 0)) if self.state else self.orig_colors  # Green if toggled on
            self.text = f'{self.text} [ON]' if self.state else self.text.split(' [')[0]  # Add "[ON]" to text if toggled
            self.check_hover((0,0))

        def toggle_side(self, wind_dir):
            self.state = not self.state
            self.text = "Right side wind" if not self.state else "Left side wind"
            return -wind_dir

        
          

    pygame.init()    
    SCREENSIZE = 1200, 800
    screen = pygame.display.set_mode(SCREENSIZE)
    clock = pygame.time.Clock()

    # GUI Options
    weather_options = ['rain', 'acid rain', 'snow', 'hail', 'lightning', 'fog']
    wind_speeds = {'None':0, 'Low': 2, 'Medium': 5, 'High': 10, 'Extreme': 20}
    wind_dir = +1 #Is either +1 or -1 depending on side_wind_button
    selected_weather = []
    wind_speed = 0  # Default to None
    pixel = False

    # Create buttons
    weather_buttons = []
    y_offset = 50
    for option in weather_options:
        weather_buttons.append(Button(option, (50, y_offset), (200, 50)))
        y_offset += 60

    wind_buttons = []
    y_offset = 50
    for speed in wind_speeds.keys():
        wind_buttons.append(Button(speed, (300, y_offset), (200, 50)))
        y_offset += 60
    wind_buttons[0].toggle()

    pixel_button     = Button("Pixel Mode", (550, 50), (200, 50))
    side_wind_button = Button("Right side wind", (550, 150), (200, 50))
    start_button     = Button("Start Simulation", (550, 450), (200, 50), colors=((0, 100, 0), (0, 150, 0)))
    
    all_buttons = weather_buttons + wind_buttons
    all_buttons.extend([pixel_button, side_wind_button, start_button])

    # State booleans
    simulation_on = False
    running = True

    # Load images
    bgrnd_px   = pygame.image.load(f'assets/imgpix.webp').convert_alpha() 
    bgrnd_norm = pygame.image.load(f'assets/img.webp').convert_alpha() 
    bgrnd_px   = pygame.transform.scale(bgrnd_px, (SCREENSIZE[0], SCREENSIZE[1]))
    bgrnd_norm = pygame.transform.scale(bgrnd_norm, (SCREENSIZE[0], SCREENSIZE[1]))

    # Run the GUI loop
    while running:
        screen.fill((30, 30, 30))

        # Draw buttons 
        for button in all_buttons:
            button.draw(screen)

        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                running = False
                return

            elif event.type == pygame.MOUSEMOTION:
                # Check hover only on MOUSEMOTION
                for button in all_buttons:
                    button.check_hover(mouse_pos)


            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check clicks only on MOUSEBUTTONDOWN
                for button in weather_buttons:
                    if button.is_clicked(mouse_pos):
                        button.toggle()

                for button in wind_buttons:
                    if button.is_clicked(mouse_pos):
                        # Only one wind speed can be selected
                        for b in wind_buttons:
                            b.state = False
                            b.colors = b.orig_colors
                            b.text = b.text.split(' [')[0]
                        button.toggle()
                        wind_speed = wind_speeds[button.text.split(' [')[0]]
                
                if side_wind_button.is_clicked(mouse_pos):
                    wind_dir = side_wind_button.toggle_side(wind_dir)

                if pixel_button.is_clicked(mouse_pos):
                    pixel_button.toggle()
                    pixel = pixel_button.state

                if start_button.is_clicked(mouse_pos):
                    selected_weather = [button.text.split(' [')[0] for button in weather_buttons if button.state]
                    menu_on = False
                    simulation_on = True
                 
        # Start the weather simulation if the user presses the Enter key
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            selected_weather = [button.text.split(' [')[0] for button in weather_buttons if button.state]
            simulation_on = True


        if simulation_on:
            weather = Weather(screen, weather_types=selected_weather, wind_speed=wind_speed * wind_dir, pixel=pixel)
            
            print("simulating")
            while simulation_on:

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return

                    # Check if the user presses Enter to return to the selection screen
                    elif event.type == pygame.KEYDOWN:
                        simulation_on = False
                        menu_on = True
                        print("key pressed")
                
                screen.blit(bgrnd_px, (0,0)) if pixel else screen.blit(bgrnd_norm, (0,0)) 
                
                weather.update()
                pygame.display.flip()
                clock.tick(60)
                
                if menu_on:
                    # Reset the selected weather options
                    for button in weather_buttons:
                        button.state = False
                        button.colors = button.orig_colors
                        button.text = button.text.split(' [')[0]

                    # Return to the button selection screen
                    menu_on = True

        else:
            pygame.display.flip()
            clock.tick(60)

if __name__ == '__main__':
    main()
