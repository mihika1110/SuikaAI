import pyglet as pg
import pymunk as pm
import numpy as np

from constants import *
from bocal import Bocal
from fruit import ActiveFruits
import gui
from collision import CollisionHelper
import utils
from preview import FruitQueue
import sprites
from suika_agent import SuikaAgent
from welcome_screen import WelcomeScreen


class Autoplayer(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self._rate = 0
        self.disable()

    def get_rate(self):
        return self._rate

    def enable(self):
        if( not self._enabled ):
            self._enabled = True
            if( self._rate==0 ):
                self._rate = AUTOPLAY_INITIAL_RATE

    def disable(self):
        self._time_debt = 0
        self._enabled = False

    def toggle(self):
        if( not self._enabled ):
             self.enable()
        else:
            self.disable()

    def adjust_rate( self, adj ):
        self._time_debt = 0
        if( adj>0 and self._rate==0 ):
            self._rate = AUTOPLAY_INITIAL_RATE
        else:
            self._rate = max( 0, self._rate+adj )
        print(f"autoplayer rate = {self._rate} fruits/sec")

    def step(self, dt):
        # called each frame
        # returns the number of fruits to drop on the current frame
        if( not self._enabled or self._rate == 0 ):
            return 0
        t = self._time_debt + dt
        nb = int( t * self._rate )
        self._time_debt = t - nb/self._rate
        return nb


class MouseState(object):
    """
    Utility to track mouse state (position, buttons)
    """

    def __init__(self, window):
        # callbacks
        self.on_autofire_stop = None
        self.on_fruit_drag = None

        window.push_handlers( 
            self.on_mouse_motion,
            self.on_mouse_drag,
            self.on_mouse_press,
            self.on_mouse_release )
        self.reset()

    def reset(self):
        self._autofire_on = False
        self._left_click_start = None
        self.position = None


    @property
    def autofire(self):
        if( not self._left_click_start ):
            return False
        if( not self._autofire_on ):
            t = utils.now() - self._left_click_start
            if( t > AUTOFIRE_DELAY ):
                self._autofire_on = True
        return self._autofire_on


    def on_mouse_press(self, x, y, button, modifiers):
        ret = pg.event.EVENT_UNHANDLED

        if( self._autofire_on ):                     # stop autofire/autoplay when active
            self._autofire_on = False
            if( self.on_autofire_stop ):
                self.on_autofire_stop()
            ret = pg.event.EVENT_HANDLED             # to avoid dropping a fruit on the next part
        
        if( (button & pg.window.mouse.LEFT) ):      # note the moment of click start
            self._left_click_start = utils.now()
            self.position = (x, y)
        return ret


    def on_mouse_release(self, x, y, button, modifiers):
        if( (button & pg.window.mouse.LEFT) ):
            if( not self._autofire_on ):
                self._left_click_start = None


    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if( (buttons & pg.window.mouse.LEFT) ):
            #print( f"on_mouse_drag(x={x}, y={y}, dx={dx} dy={dy})")
            self._set_pos(x, y)
    

    def on_mouse_motion(self, x, y, dx, dy):
        self._set_pos(x, y)


    def _set_pos(self, x, y):
        self.position = (x, y)
        if( self.on_fruit_drag ):
            self.on_fruit_drag( x, y )


class SuikaWindow(pg.window.Window):
    def __init__(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT):
        # Initialize all attributes before creating window
        self._is_gameover = False
        self._is_paused = False
        self._autoplay_txt = ""
        self._is_mouse_shake = False
        self._is_benchmark_mode = False
        self._dragged_fruit = None
        self.game_started = False
        
        # Initialize window
        super().__init__(width=width, height=height, resizable=True)
        
        # Create welcome screen
        self.welcome_screen = WelcomeScreen(width, height, self.start_game)
        
        # Initialize game objects
        self._space = pm.Space()
        self._space.gravity = (0, GRAVITY)
        self._bocal = Bocal(space=self._space, **utils.bocal_coords(window_w=width, window_h=height))
        self._preview = FruitQueue(cnt=PREVIEW_COUNT)
        self._fruits = ActiveFruits(space=self._space, width=width, height=height)
        self._countdown = utils.CountDown()
        self._gui = gui.GUI(window_width=width, window_height=height)
        self._collision_helper = CollisionHelper(self._space)
        self._autoplayer = Autoplayer()
        
        # AI agent setup
        self.ai_agent = SuikaAgent()
        self.ai_enabled = False
        self.training_mode = False
        self.last_state = None
        self.last_action = None
        self.cumulative_reward = 0
        self.episode = 0
        
        # Initialize display metrics
        self.display_fps = utils.Speedmeter()
        self.pymunk_fps = utils.Speedmeter(bufsize=int(3/PYMUNK_INTERVAL))
        
        # Initialize mouse handling
        self._mouse_state = MouseState(self)
        self._mouse_state.on_autofire_stop = self._autoplayer.disable
        
        # Schedule updates
        pg.clock.schedule_interval(self.simulation_tick, interval=PYMUNK_INTERVAL)
        pg.clock.schedule_interval(self.autoplay_tick, interval=AUTOPLAY_INTERVAL_BASE)
        pg.clock.schedule_interval(self.ai_tick, interval=0.5)
        
        # Set window properties
        self.set_caption("Suika Game")
        self.set_minimum_size(
            width=2 * BOCAL_MARGIN_SIDE + BOCAL_MIN_WIDTH,
            height=BOCAL_MARGIN_TOP + BOCAL_MARGIN_BOTTOM + BOCAL_MIN_HEIGHT
        )
        
        # Reset game state
        self.reset_game()

    def reset_game(self):
        self._is_gameover = False
        self._is_paused = False
        self._autoplay_txt = ""
        self._is_mouse_shake = False
        self._is_benchmark_mode = False
        self._dragged_fruit = None
        self._bocal.reset()
        self._preview.reset()
        self._fruits.reset()
        self._collision_helper.reset()
        self._countdown.reset()
        self._gui.reset()
        self._autoplayer.reset()
        self._mouse_state.reset()
        self.prepare_next()

    def start_game(self):
        """Called when user clicks start on welcome screen"""
        self.game_started = True
        self.reset_game()
        print("\n=== Game Started! ===")
        print("Controls:")
        print("- Left Click: Drop fruit")
        print("- Right Click: Shoot fruit")
        print("- I: Toggle AI mode")
        print("- T: Toggle training mode")
        print("- ESC: Quit game\n")
        
        # Ensure the game is properly initialized
        self._space.gravity = (0, GRAVITY)
        self._bocal.reset()
        self._preview.reset()
        self._fruits.reset()
        self._collision_helper.reset()
        self._countdown.reset()
        self._gui.reset()
        self._autoplayer.reset()
        self._mouse_state.reset()
        self.prepare_next()
        
        # Clear any existing welcome screen
        if hasattr(self, 'welcome_screen'):
            self.welcome_screen = None

    def toggle_benchmark_mode( self ):
        pg.clock.unschedule( self.simulation_step )
        self._is_benchmark_mode = not self._is_benchmark_mode
        if( self._is_benchmark_mode ):
            pg.clock.schedule( self.simulation_step )
        else:
            pg.clock.schedule_interval( self.simulation_step, interval=PYMUNK_INTERVAL )

    def prepare_next(self):
        kind = self._preview.get_next_fruit()
        self._fruits.prepare_next( kind=kind )


    def drop(self, cursor_x, nb=1):
        for _ in range(nb):
            next = self._fruits.peek_next()
            if( not next ):
                return
            margin=next.radius + WALL_THICKNESS/2 + 1

            # position of the mouse or random if x = None 
            if( cursor_x is None ):
                pos = self._bocal.drop_point_random( margin=margin )
            else:
                pos = self._bocal.drop_point_cursor( cursor_x, margin=margin )

            if( not pos ):            # pos==None if click is outside container
                return
            self._fruits.drop_next(pos)
            self.prepare_next()


    def autoplay_tick(self, dt):
        if( self._is_paused or self._is_gameover ):
            self._autoplay_txt = ""
            return
        msg = []
        nb = self._autoplayer.step(dt)
        # autofire ( = autoplay controlled by mouse )
        if( self._mouse_state.autofire ):
            self._autoplayer.enable()   # active autoplay
            pos = self._mouse_state.position    # None if pointer is outside window
            if(pos):
                self.drop(cursor_x=self._mouse_state.position[0], nb=nb) 
                msg.append(f"AUTOFIRE")
        # autoplay ( drop on random location )
        elif( self._autoplayer._enabled):
            self.drop(nb=nb, cursor_x=None)
            msg.append(f"AUTOPLAY")

        # add autoplay/autofire rate only if active.
        if(len(msg)):
            msg.append(f"{self._autoplayer.get_rate()} fruits/sec")
        self._autoplay_txt = ' '.join(msg)


    def gameover(self):
        """ Actions in case of game over
        """
        print("GAMEOVER")
        self._is_gameover = True    # inhibit game actions
        self._autofire_on = False
        self._fruits.gameover()
        self._gui.show_gameover()


    def toggle_pause(self):
        assert( not self._is_gameover )
        self._is_paused = not self._is_paused


    def set_mouse_shake( self, activate ):
        self._is_mouse_shake = bool(activate)


    def fruit_drag_start(self):
        # pass the fruit under the mouse in DRAG_MODE
        cursor = self._mouse_state.position
        self._dragged_fruit = self.find_fruit_at( *cursor )
        if( self._dragged_fruit) :
            self._dragged_fruit.drag_mode( cursor )   # set_mode


    def fruit_drag_stop(self):
        if( self._dragged_fruit ):
            self._dragged_fruit.drag_mode( None )   # set_mode
            self._dragged_fruit = None


    def find_fruit_at(self, x, y):
        qi = self._space.point_query( (x, y), max_distance=0, shape_filter=pm.ShapeFilter() )
        if( len(qi)==0 ):
            return None
        if( len(qi) > 1):
            print("WARNING: Multiple overlapping fruits detected")
        if( not hasattr( qi[0].shape, 'fruit' )):
           return None     # shape is not a fruit (e.g. bocal)
        return qi[0].shape.fruit


    def shoot_fruit(self, x, y):
        print(f"right click x={x} y={y}")
        f = self.find_fruit_at(x, y)
        if( not self._is_gameover and f ):
            f.explose()


    def spawn_in_bocal(self, kind, bocal_coords):
        position = self._bocal.to_world( bocal_coords )
        self._fruits.spawn( kind, position )


    def simulation_tick(self, dt):
        """Advance one physics step
        called by window.on_draw()
        """
        self.pymunk_fps.tick_rel(dt)
        if( self._is_paused ):
            return

        # update bocal elements position
        self._bocal.step(dt)
        # update dragged fruit in DRAG_MODE
        if( self._dragged_fruit ):
            self._dragged_fruit.drag_to( self._mouse_state.position, dt)
        # prepare collision handler
        self._collision_helper.reset()
        # execute 1 physics step
        self._space.step( PYMUNK_INTERVAL )  

        # modify fruits based on detected collisions
        self._collision_helper.process( 
            spawn_func=self.spawn_in_bocal, 
            world_to_bocal_func=self._bocal.to_bocal )
        # clean up
        self._fruits.cleanup()


    def update(self):
        # handle countdown in case of overflow
        if( not self._bocal.is_tumbling):
            ids = self._bocal.fruits_sur_maxline()
            self._countdown.update( ids )

        # update display and detect game end
        countdown_val, countdown_txt = self._countdown.status()
        if( countdown_val < 0 and not self._is_gameover ):
            self.gameover()

        # order of conditions defines message priority
        game_status = ""
        if( True ):               game_status = self._autoplay_txt
        if( countdown_txt ):      game_status = countdown_txt
        if( self._is_paused ):    game_status = "PAUSE"
        if( self._is_gameover ):  game_status = "GAME OVER"

        # Update display with training stats if in training mode
        if self.training_mode:
            self._gui.update_dict({
                gui.TOP_LEFT: f"Score: {self._fruits._score}",
                gui.TOP_RIGHT: f"FPS {self.pymunk_fps.value:.0f} / {self.display_fps.value:.0f}",
                gui.TOP_CENTER: f"Epsilon: {self.ai_agent.epsilon:.3f} | Best: {self.ai_agent.best_score} | Ep: {self.episode}"
            })
        else:
            self._gui.update_dict({
                gui.TOP_LEFT: f"score {self._fruits._score}",
                gui.TOP_RIGHT: f"FPS {self.pymunk_fps.value:.0f} / {self.display_fps.value:.0f}",
                gui.TOP_CENTER: game_status
            })


    def end_application(self):
        # TODO : release resources more cleanly
        self.close()


    def on_draw(self):
        self.clear()
        if not self.game_started:
            self.welcome_screen.draw()
        else:
            # Update game objects
            self._fruits.update()
            self._preview.update()
            self._bocal.update()
            self.update()

            # Draw game
            sprites.batch().draw()
            self.display_fps.tick()


    def on_key_press(self, symbol, modifiers):
        if symbol == pg.window.key.ESCAPE:         # ESC closes the game in all cases
            self.end_application()
        elif symbol == pg.window.key.I:            # 'I' for AI
            self.toggle_ai()
        elif symbol == pg.window.key.T:            # 'T' for training mode
            self.toggle_training()
        elif not self.ai_enabled:  # Only allow these controls when AI is disabled
            if symbol == pg.window.key.R:          # Reset game
                self.reset_game()
            elif symbol == pg.window.key.A:        # A controls autoplay
                self._autoplayer.toggle()
            elif symbol == pg.window.key.S:        # S shakes the bocal automatically
                self._bocal.shake_auto()
            elif symbol == pg.window.key.SPACE:    # SPACE puts in MOUSE_SHAKE mode
                self._bocal.shake_mouse()
                self.push_handlers(self._bocal.on_mouse_motion)
            elif symbol == pg.window.key.M:        # move a fruit to the mouse
                self.fruit_drag_start()
            elif symbol == pg.window.key.P:        # P pauses the game
                self.toggle_pause()
            elif symbol == pg.window.key.G:        # G forces a gameover in progress
                self.gameover()
            elif symbol == pg.window.key.B:        # Benchmark mode
                self.toggle_benchmark_mode()

    def on_key_release(self, symbol, modifiers):
        if(symbol == pg.window.key.SPACE):          # stop manual shaking
            self._bocal.shake_stop()
            self.pop_handlers()
        elif(symbol == pg.window.key.S):            # stop automatic shaking
            self._bocal.shake_stop()
        elif(symbol == pg.window.key.M):            # release the fruit after moving to the mouse
            self.fruit_drag_stop()


    def on_mouse_press(self, x, y, button, modifiers):
        if not self.game_started:
            self.welcome_screen.on_button_click(x, y)
            return

        if self._is_gameover:
            self.reset_game()
        elif (button & pg.window.mouse.LEFT):
            self.drop(x)
        elif (button & pg.window.mouse.RIGHT):
            self.shoot_fruit(x, y)


    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        #print(f"on_mouse_scroll(x={x} y={y} scroll_x={scroll_x} scroll_y={scroll_y}    => lvl={self._autoplay_level}")
        self._autoplayer.adjust_rate(scroll_y)


    def on_resize(self, width, height):
        """Handle window resize events"""
        if hasattr(self, '_bocal'):  # Check if _bocal exists before using it
            self._bocal.on_resize(**utils.bocal_coords(window_w=width, window_h=height))
            self._fruits.on_resize(width, height)
            self._preview.on_resize(width, height)
            self._gui.on_resize(width, height)
        
        # Update welcome screen if it exists
        if hasattr(self, 'welcome_screen'):
            self.welcome_screen = WelcomeScreen(width, height, self.start_game)
            
        # Update window
        super().on_resize(width, height)

    def get_game_state(self):
        """Get current game state for AI"""
        return self._fruits._fruits

    def get_reward(self):
        """Calculate reward based on game state"""
        reward = 0
        
        # Reward for score (increased weight)
        reward += self._fruits._score * 0.5
        
        # Penalty for fruits above red line (increased penalty)
        fruits_above = len(self._bocal.fruits_sur_maxline())
        reward -= fruits_above * 10
        
        # Big penalty for game over (increased penalty)
        if self._is_gameover:
            reward -= 200
            
        # Reward for successful merges (new)
        if hasattr(self, '_last_score'):
            score_diff = self._fruits._score - self._last_score
            if score_diff > 0:
                reward += score_diff * 2  # Extra reward for successful merges
        self._last_score = self._fruits._score
            
        return reward

    def toggle_ai(self):
        """Toggle AI control"""
        self.ai_enabled = not self.ai_enabled
        if self.ai_enabled:
            print("\n=== AI Mode Enabled ===")
            print("AI will play normally")
            print("Press T to enable training mode")
        else:
            print("\n=== AI Mode Disabled ===")
            # Disable training mode when AI is disabled
            if self.training_mode:
                self.toggle_training()

    def toggle_training(self):
        """Toggle AI training mode"""
        if not self.ai_enabled:
            print("\nEnable AI mode first (press I)!")
            return
            
        self.training_mode = not self.training_mode
        if self.training_mode:
            print("\n=== Training Mode Enabled ===")
            print("AI is now learning and improving")
            print("Controls:")
            print("- Press T again to disable training")
            print("- Press I to disable AI completely")
            print("\nCurrent Statistics:")
            print(f"Total Episodes: {self.episode}")
            print(f"Best Score: {self.ai_agent.best_score}")
            print(f"Current Exploration Rate: {self.ai_agent.epsilon:.3f}")
            # Speed up the AI decision interval in training mode
            pg.clock.unschedule(self.ai_tick)
            pg.clock.schedule_interval(self.ai_tick, interval=0.1)
        else:
            print("\n=== Training Mode Disabled ===")
            print("AI is now playing normally")
            # Restore normal AI decision interval
            pg.clock.unschedule(self.ai_tick)
            pg.clock.schedule_interval(self.ai_tick, interval=0.5)

    def ai_tick(self, dt):
        """AI decision making loop"""
        if not self.ai_enabled or self._is_paused:
            return

        # If game is over, handle based on mode
        if self._is_gameover:
            if self.training_mode:
                # Update training statistics
                self.ai_agent.update_training_stats(self.episode, self._fruits._score, self.cumulative_reward)
                self.episode += 1
                self.cumulative_reward = 0
                # Reset game for next episode
                self.reset_game()
            else:
                # In normal AI mode, just reset the game
                self.reset_game()

        current_state = self.get_game_state()
        
        # Get reward for previous action
        if self.last_state is not None:
            reward = self.get_reward()
            self.cumulative_reward += reward
            
            # Train the agent only in training mode
            if self.training_mode:
                self.ai_agent.train(
                    self.last_state,
                    self.last_action,
                    reward,
                    current_state,
                    self._is_gameover
                )

        # Get new action from agent
        action = self.ai_agent.get_action(current_state, self.width)
        
        # Execute action
        self.drop(action)
        
        # Save state and action
        self.last_state = current_state
        self.last_action = action

def main():
    pg.resource.path = ['assets/']
    pg.resource.reindex()
    window = SuikaWindow()
    pg.app.run()

if __name__ == '__main__':
    main()

