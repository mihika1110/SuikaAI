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
        
        # Create background that covers entire window
        self.background = shapes.Rectangle(
            x=0, y=0,
            width=width,
            height=height,
            color=(41, 128, 185, 255),  # Nice blue color
            batch=self.batch
        )
        
        # Create decorative floating circles
        self.circles = []
        circle_colors = [
            (255, 255, 255, 30),
            (255, 255, 255, 40),
            (255, 255, 255, 50),
            (255, 255, 255, 40),
            (255, 255, 255, 30),
        ]
        
        # Calculate circle positions based on screen size
        circle_positions = [
            (0.2, 0.6),  # Left
            (0.35, 0.65),  # Center-left
            (0.5, 0.7),   # Center
            (0.65, 0.65), # Center-right
            (0.8, 0.6),   # Right
        ]
        
        for i, (x_ratio, y_ratio) in enumerate(circle_positions):
            circle = shapes.Circle(
                x=width * x_ratio,
                y=height * y_ratio,
                radius=min(width, height) * 0.1,  # Responsive size
                color=circle_colors[i],
                batch=self.batch
            )
            self.circles.append(circle)
        
        # Create main title
        title_size = min(width // 12, height // 6)  # Responsive font size
        self.title = Label(
            text='HELLO!',
            font_name='Arial',
            font_size=title_size,
            x=width//2,
            y=height * 0.6,
            anchor_x='center',
            anchor_y='center',
            batch=self.batch,
            color=(255, 255, 255, 255)
        )
        
        # Create subtitle
        subtitle_size = min(width // 20, height // 10)
        self.subtitle = Label(
            text='Welcome to Suika World',
            font_name='Arial',
            font_size=subtitle_size,
            x=width//2,
            y=height * 0.5,
            anchor_x='center',
            anchor_y='center',
            batch=self.batch,
            color=(255, 255, 255, 255)
        )
        
        # Create start button (positioned at bottom right)
        button_width = min(width // 5, 240)  # Cap maximum width
        button_height = min(height // 12, 70)  # Cap maximum height
        margin = min(width, height) * 0.05  # Responsive margin
        
        button_x = width - button_width - margin
        button_y = margin
        
        # Button glow
        self.button_glow = shapes.Rectangle(
            x=button_x - 5,
            y=button_y - 5,
            width=button_width + 10,
            height=button_height + 10,
            color=(255, 255, 255, 100),
            batch=self.batch
        )
        
        # Main button
        self.button = shapes.Rectangle(
            x=button_x,
            y=button_y,
            width=button_width,
            height=button_height,
            color=(46, 204, 113, 255),  # Nice green color
            batch=self.batch
        )
        
        # Button text
        button_text_size = min(width // 30, height // 20)
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
        
        # Animate circles with gentle floating motion
        for i, circle in enumerate(self.circles):
            # Calculate base position
            base_y = self.height * (0.6 + (i * 0.025))
            # Add floating animation
            offset = math.sin(self.time * 0.8 + i * 0.5) * (self.height * 0.02)
            circle.y = base_y + offset
            
            # Animate circle opacity
            alpha = int(128 + math.sin(self.time * 1.2 + i) * 50)
            circle.color = (*circle.color[:3], alpha)
        
        # Animate title with subtle float
        self.title.y = self.height * 0.6 + math.sin(self.time * 1.5) * (self.height * 0.015)
        
        # Animate subtitle with offset wave
        self.subtitle.y = self.height * 0.5 + math.sin(self.time * 1.5 + 1) * (self.height * 0.01)
        
        # Animate button glow
        glow_intensity = 150 + math.sin(self.time * 3) * 70
        self.button_glow.color = (255, 255, 255, int(glow_intensity))
        
        # Animate button color
        hue = (math.sin(self.time) + 1) / 2
        self.button.color = (int(46 + hue * 30), int(204 + hue * 20), int(113 + hue * 15), 255)
    
    def on_button_click(self, x, y):
        # Check if click is within button bounds
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
