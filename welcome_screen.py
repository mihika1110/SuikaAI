import pyglet as pg
from pyglet import shapes
from pyglet.text import Label
import math

class WelcomeScreen:
    def __init__(self, width, height, on_start):
        self.width = width
        self.height = height
        self.on_start = on_start
        self.batch = pg.graphics.Batch()
        self.time = 0
        
        # Create gradient background
        self.background = shapes.Rectangle(
            x=0, y=0,
            width=width,
            height=height,
            color=(180, 230, 180, 255),  # Light green gradient color
            batch=self.batch
        )
        
        # Create wooden frame
        frame_margin = min(width, height) * 0.15
        self.frame = shapes.Rectangle(
            x=frame_margin,
            y=frame_margin,
            width=width - 2 * frame_margin,
            height=height - 2 * frame_margin,
            color=(139, 69, 19, 255),  # Brown color
            batch=self.batch
        )
        
        # Create inner frame (tan colored)
        inner_margin = frame_margin * 1.05
        self.inner_frame = shapes.Rectangle(
            x=inner_margin,
            y=inner_margin,
            width=width - 2 * inner_margin,
            height=height - 2 * inner_margin,
            color=(210, 180, 140, 255),  # Tan color
            batch=self.batch
        )
        
        # Create "Welcome to" text
        welcome_size = min(width // 16, height // 16)  # Larger size for "Welcome to"
        self.welcome_text = Label(
            text='Welcome to',
            font_name='Arial',
            font_size=welcome_size,
            x=width//2,
            y=height * 0.75,  # Position higher
            anchor_x='center',
            anchor_y='center',
            batch=self.batch,
            color=(50, 25, 0, 255)  # Dark brown color
        )
        
        # Create "SUIKA WORLD" text with smaller font
        title_size = min(width // 20, height // 8)  # Smaller size for "SUIKA WORLD"
        self.title = Label(
            text='SUIKA WORLD',
            font_name='Arial',
            font_size=title_size,
            x=width//2,
            y=height * 0.65,  # Position below "Welcome to"
            anchor_x='center',
            anchor_y='center',
            batch=self.batch,
            color=(50, 25, 0, 255)  # Dark brown color
        )
        
        # Load fruit images
        fruit_names = [
            'cerise.png',      # Cherry
            'fraise.png',      # Strawberry
            'prune.png',       # Plum
            'orange.png',      # Orange
            'abricot.png',     # Apricot
            'pomme.png',       # Apple
            'pamplemousse.png',# Grapefruit
            'ananas.png',      # Pineapple
            'melon.png',       # Melon
            'tomate.png',      # Tomato
            'pasteque.png',    # Watermelon
        ]
        
        self.fruit_sprites = []
        fruit_size = min(width, height) * 0.15
        
        # Calculate positions in two rows
        fruits_per_row = 6
        start_x = width * 0.25
        spacing_x = (width * 0.5) / (fruits_per_row - 1)
        
        # First row - moved down to accommodate title
        y_row1 = height * 0.45
        for i in range(fruits_per_row):
            if i < len(fruit_names):
                try:
                    img = pg.resource.image(fruit_names[i])
                    img.anchor_x = img.width // 2
                    img.anchor_y = img.height // 2
                    
                    scale = fruit_size / max(img.width, img.height)
                    
                    sprite = pg.sprite.Sprite(
                        img,
                        x=start_x + i * spacing_x,
                        y=y_row1,
                        batch=self.batch
                    )
                    sprite.scale = scale
                    self.fruit_sprites.append(sprite)
                except Exception as e:
                    print(f"Error loading fruit image {fruit_names[i]}: {e}")
        
        # Second row
        y_row2 = height * 0.3
        remaining_fruits = len(fruit_names) - fruits_per_row
        spacing_x2 = (width * 0.4) / (remaining_fruits - 1)
        start_x2 = width * 0.3
        
        for i in range(remaining_fruits):
            try:
                img = pg.resource.image(fruit_names[i + fruits_per_row])
                img.anchor_x = img.width // 2
                img.anchor_y = img.height // 2
                
                scale = fruit_size / max(img.width, img.height)
                
                sprite = pg.sprite.Sprite(
                    img,
                    x=start_x2 + i * spacing_x2,
                    y=y_row2,
                    batch=self.batch
                )
                sprite.scale = scale
                self.fruit_sprites.append(sprite)
            except Exception as e:
                print(f"Error loading fruit image {fruit_names[i + fruits_per_row]}: {e}")
        
        # Create start button
        button_width = min(width // 2, 400)  # Slightly narrower button
        button_height = min(height // 8, 80)  # Shorter button
        button_x = (width - button_width) // 2
        button_y = height * 0.15
        
        # Main button
        self.button = shapes.Rectangle(
            x=button_x,
            y=button_y,
            width=button_width,
            height=button_height,
            color=(34, 139, 34, 255),  # Forest green
            batch=self.batch
        )
        
        # Button text - significantly smaller
        button_text_size = min(width // 36, height // 36)  # Much smaller text size
        self.button_text = Label(
            text='START GAME',
            font_name='Arial',
            font_size=button_text_size,
            x=button_x + button_width//2,
            y=button_y + button_height//2,
            anchor_x='center',
            anchor_y='center',
            batch=self.batch,
            color=(255, 255, 255, 255)
        )
        
        # Store button dimensions for click detection
        self.button_bounds = {
            'x': button_x,
            'y': button_y,
            'width': button_width,
            'height': button_height
        }
        
        # Schedule animation updates
        pg.clock.schedule_interval(self.update, 1/60)
        
    def update(self, dt):
        self.time += dt
        
        # Gentle pulsing animation for fruits
        for i, sprite in enumerate(self.fruit_sprites):
            base_scale = min(self.width, self.height) * 0.15 / max(sprite.image.width, sprite.image.height)
            scale_factor = 1.0 + math.sin(self.time * 2 + i * 0.5) * 0.05
            sprite.scale = base_scale * scale_factor
            
            # Add gentle rotation
            sprite.rotation = math.sin(self.time * 1.5 + i * 0.7) * 5
        
        # Button color animation
        base_green = 34
        color_shift = int(math.sin(self.time * 2) * 20)
        self.button.color = (base_green, 139 + color_shift, base_green, 255)
    
    def on_button_click(self, x, y):
        if (self.button_bounds['x'] <= x <= self.button_bounds['x'] + self.button_bounds['width'] and 
            self.button_bounds['y'] <= y <= self.button_bounds['y'] + self.button_bounds['height']):
            self.on_start()
    
    def draw(self):
        self.batch.draw()
        
    def __del__(self):
        try:
            pg.clock.unschedule(self.update)
        except:
            pass
