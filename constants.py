
############ Application Appearance #############
WINDOW_HEIGHT = 1800
WINDOW_WIDTH  = 1400
BOCAL_MARGIN_TOP = 200
BOCAL_MARGIN_BOTTOM = 50
BOCAL_MARGIN_SIDE = 150
GUI_FONT_SIZE = 25
GUI_TOP_MARGIN = 10
NEXT_FRUIT_Y_POS = BOCAL_MARGIN_TOP//2   # pixels from top
PREVIEW_Y_POS =  90    # pixels from top
PREVIEW_SPRITE_SIZE = 50
PREVIEW_SLOT_SIZE = 70
PREVIEW_COUNT = 3

############### Appearance of container ############
WALL_THICKNESS = 20
WALL_COLOR = (205,200,255,255)
REDLINE_TOP_MARGIN = 170
REDLINE_THICKNESS = 2
REDLINE_COLOR= (255,20,20,255) 
BOCAL_MIN_WIDTH=300
BOCAL_MIN_HEIGHT=400

############ Physical Simulation #############
PYMUNK_INTERVAL = 1 / 120.0    
FRICTION = 1.0
GRAVITY = -981
INITIAL_VELOCITY = 1200
ELASTICITY_FRUIT = 0.05
ELASTICITY_WALLS = 0.05


############ Game animations and timings #############
AUTOPLAY_INTERVAL_BASE = 0.05       # seconds
AUTOPLAY_INITIAL_RATE = 5

PREVIEW_SHIFT_DELAY = 0.1  # seconds
AUTOFIRE_DELAY = 0.5       # secondes
SHAKE_FREQ_MIN = 1.5       # Hz
SHAKE_FREQ_MAX = 5         # Hz
SHAKE_ACCEL_DELAY = 0.5    # seconds
SHAKE_AMPLITUDE_X = 50
SHAKE_AMPLITUDE_Y = 50
SHAKE_RETURN_SPEED = 0.25      # coefficient of return speed to the ref position
SHAKE_MOUSE_SPEED = 0.5       # Manual shaking speed coefficient
TUMBLE_FREQ = 0.25    # Hz
COUNTDOWN_DISPLAY_LIMIT = 3.0   # seconds
GAMEOVER_DELAY = 4.0            # seconds
GAMEOVER_ANIMATION_START = 5         # seconds
GAMEOVER_ANIMATION_INTERVAL = 0.3    # seconds


############# fruit animation settings ################
BLINK_DELAY = 1.0          # seconds
BLINK_FREQ  = 6.0          # Hz
FADEOUT_DELAY = 0.5        # seconds
FADEIN_DELAY = 0.08        # seconds
FADEIN_OVERSHOOT = 1.15    # ratio
FADE_SIZE = 0.2            # ratio for the starting (resp. ending) size of the fade-in (resp. fadeout)
EXPLOSION_DELAY = 0.3      # seconds
MERGE_DELAY = 0.1          # seconds
SPAWN_DELAY = 0.3          # seconds


# Identifiers to dispatch collisions on game logic
# fruits have a COLLISION_TYPE equal to their kind ( fruit.kind )
COLLISION_TYPE_WALL_BOTTOM = 1000
COLLISION_TYPE_WALL_SIDE = 1001
COLLISION_TYPE_MAXLINE = 1002
COLLISION_TYPE_FIRST_DROP = 1003

# categories for fast collision filtering
CAT_WALLS          = 1 << 0
CAT_MAXLINE        = 1 << 1
CAT_FRUIT_WAIT     = 1 << 2
CAT_FRUIT_DROP     = 1 << 3
CAT_FRUIT          = 1 << 4
CAT_FRUIT_MERGE    = 1 << 5
CAT_FRUIT_REMOVED  = 1 << 6

