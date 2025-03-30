import math, random
import pymunk as pm
from constants import *
from sprites import LineSprite
import utils


LEFT = "left"
RIGHT = "right"
BOTTOM = "bottom"
TOP= "top"
MAXLINE = "maxline"

SHAKE_OFF='off'
SHAKE_AUTO='auto'
SHAKE_MOUSE='mouse'
SHAKE_STOPPING='stopping'

TUMBLE_OFF='off'
TUMBLE_ONCE='once'


WALLS_DAMPING = 10     # 1 = no damping, 2 = timestep/2, etc...

class BoxElement(object):
    """ Physical pymunk shape associated with a graphical object
       Base class for container elements (Wall, Maxline)
    """
    def __init__(self, bocal_w, bocal_h, collision_type, thickness ):
        # fundamental dimensions of the object relative to self.body
        self._length, self._local_angle = self.dimensions( bocal_w, bocal_h )
        # coordinates of object endpoints in self.body's reference frame
        (a,b) = self.local_coords()

        # pyglet graphical object
        self.line = self.make_sprite(a,b)

        # pymunk physical object with a segment collision shape
        self.body = pm.Body(body_type=pm.Body.KINEMATIC)
        self.segment = pm.Segment( self.body, a, b, radius=thickness/2 )
        self.segment.collision_type = collision_type


    def local_coords(self):
        """coords in the reference frame of self.body
        """
        a0 = pm.Vec2d(-self._length/2, 0)
        b0 = pm.Vec2d(+self._length/2, 0)
        a = a0.rotated(self._local_angle)
        b = b0.rotated(self._local_angle)
        return (a,b)


    def world_coords(self):
        (a_local, b_local) = self.local_coords()
        a = self.body.local_to_world( a_local )
        b = self.body.local_to_world( b_local )
        return (a, b)


    def on_resize(self, bocal_w, bocal_h):
        """ Container dimension change
        """
        # update sprite dimensions - applied in self.update()
        self._length, self._local_angle = self.dimensions( bocal_w, bocal_h )
        # update pymunk segment dimensions in local coordinates (only changes length)
        (a,b) = self.local_coords()
        self.segment.unsafe_set_endpoints(a, b)


    def move_to(self, position, angle, dt):
        """ Modify body velocity to place it at the required position
        """
        # angle is the body angle in physical simulation
        # do not confuse with self._local_angle
        d_pos = position - self.body.position
        d_angle = (angle - self.body.angle) % (2*math.pi)

        self.body.velocity = pm.Vec2d(0,0)
        self.body.angular_velocity = 0
        if( (dt > 0.000001) ):
            if( d_pos.length > 0.000001 ):
                self.body.velocity = d_pos / (dt * WALLS_DAMPING)
            if( d_angle > 0.000001 ):
                self.body.angular_velocity = d_angle / (dt * WALLS_DAMPING)

    def update(self):
        """ Met a jour l'objet graphique à partir de la simulation physique
        """
        (a, b) = self.world_coords()
        self.line.x, self.line.y = round(a[0]), round(a[1])
        self.line.x2, self.line.y2 = round(b[0]), round(b[1])


    def add_to_space(self, space):
        space.add( self.body, self.segment )


    # methodes implementées dans les sous classes
    def bocal_position_func(self, w, h): 
        """ Element position relative to container center
        """
        raise NotImplementedError("Instantiate a derived Wall or MaxLine class")
    
    def make_sprite(self, a, b):
        """ Create the pyglet graphical object
        """
        raise NotImplementedError("Instantiate a derived Wall or MaxLine class")

    def dimensions(self, width, height):
        """ Return length and orientation based on container dimensions
        """
        raise NotImplementedError("Instantiate a derived Wall or MaxLine class")
    

class Wall( BoxElement ):
    def __init__(self, bocal_w, bocal_h, collision_type):
        super().__init__( bocal_w=bocal_w, 
                          bocal_h=bocal_h,
                          thickness=WALL_THICKNESS,
                          collision_type=collision_type)
        self.segment.filter= pm.ShapeFilter( categories=CAT_WALLS, 
                                            mask=pm.ShapeFilter.ALL_MASKS() )
        self.segment.elasticity = ELASTICITY_WALLS
        self.segment.friction = FRICTION

    def make_sprite(self, a, b):
        return LineSprite.wall( a, b )


class HorizontalWall(Wall):
    def __init__(self, bocal_w, bocal_h):
        super().__init__( bocal_w=bocal_w, 
                          bocal_h=bocal_h,
                          collision_type=COLLISION_TYPE_WALL_BOTTOM )

    def dimensions(self, bocal_w, bocal_h):
        """ wall segment dimensions from bocal size
        """
        length = bocal_w
        local_angle = 0
        return (length, local_angle)
    
class VerticalWall(Wall):
    def __init__(self, bocal_w, bocal_h):
        super().__init__( bocal_w=bocal_w, 
                          bocal_h=bocal_h, 
                          collision_type=COLLISION_TYPE_WALL_SIDE )

    def dimensions(self, bocal_w, bocal_h):
        """ wall segment dimensions from bocal size
        """
        length = bocal_h
        local_angle = math.pi / 2
        return (length, local_angle)
    

class BottomWall(HorizontalWall):
    def bocal_position_func(self,w,h):
        return (0, -h/2)

class TopWall(HorizontalWall):
    def bocal_position_func(self,w,h):
        return (0, +h/2)

class LeftWall(VerticalWall):
    def bocal_position_func(self, w, h):
        return (-w/2, 0)

class RightWall(VerticalWall):
    def bocal_position_func(self, w, h):
        return (+w/2, 0)


class MaxLine( BoxElement ):
    """ Maximum level line in the container
    """
    def __init__(self, bocal_w, bocal_h ):
        super().__init__( bocal_w=bocal_w,
                          bocal_h=bocal_h,
                          thickness=REDLINE_THICKNESS,
                          collision_type=COLLISION_TYPE_MAXLINE)
        self.segment.filter= pm.ShapeFilter( categories=CAT_MAXLINE, 
                                            mask=pm.ShapeFilter.ALL_MASKS() ^ CAT_WALLS )
        self.segment.sensor = True

    def bocal_position_func(self, w, h):
        return (0, h/2-REDLINE_TOP_MARGIN)

    def dimensions(self, bocal_w, bocal_h):
        length = bocal_w
        local_angle=0
        return (length, local_angle)

    def make_sprite(self, a, b):
        return LineSprite.redline( a, b )



class DropZone(object):
    """Calculations for fruit drop locations inside the container
    """
    def __init__(self, bocal_body, width, height):
        self._bocal_body = bocal_body
        self.on_resize(width, height)

    def on_resize(self, width, height):
        y = height/2 - REDLINE_TOP_MARGIN//2
        self._a = pm.Vec2d(-width/2, y)
        self._b = pm.Vec2d(+width/2, y)


    def _drop_point_interpolate(self, r):
        point = self._a + (self._b - self._a) * r
        return  self._bocal_body.local_to_world( point )

    def drop_point_cursor(self, x_cursor, margin ):
        """ Returns
        either the drop point of a fruit based on the clicked point
        or None if the point is outside the container
        """
        (x_left, y_left) = self._bocal_body.local_to_world( self._a )
        (x_right, y_right) = self._bocal_body.local_to_world( self._b )

        #  r = normalized abscissa on the dropline
        if( abs(x_right - x_left) > 1.0 ):
            r = (x_cursor - x_left)  / ( x_right - x_left )
        else:
            r = 0.5    # special case for horizontal container, otherwise division by 0

        if( r < 0 or r > 1 ):
            print("Click outside the container")
            return None

        # adjust drop point so fruit doesn't overflow
        if( margin ):
            r = max( margin, r)
            r = min( 1 - margin, r)

        return self._drop_point_interpolate( r )

    def drop_point_random(self, margin):
        """ Returns a position
        either the drop point of a fruit based on the clicked point
        or None if the point is outside the container
        """
        return self._drop_point_interpolate( margin + (1 - 2*margin) * random.random() )


def _make_walls( space, width, height ):
    walls = {
        LEFT:   LeftWall(bocal_w=width, bocal_h=height),
        RIGHT:  RightWall(bocal_w=width, bocal_h=height), 
        BOTTOM: BottomWall(bocal_w=width, bocal_h=height),
        TOP:    TopWall(bocal_w=width, bocal_h=height), 
        MAXLINE: MaxLine(bocal_w=width, bocal_h=height),
    }
    for w in walls.values():
        w.add_to_space( space )
    return walls


class Bocal(object):
    """ utilitaire pour creer les parois de l'espace de jeu (space)
    """
    def __init__(self, space, center, bocal_w, bocal_h):
        # Create a static body for the container
        self._body = pm.Body(body_type=pm.Body.STATIC)  # Changed to STATIC
        self._position_ref = center
        self._width_ref = bocal_w
        self._height_ref = bocal_h
        self._body.position = center  # Set initial position immediately
        space.add(self._body)
 
        self._walls = _make_walls(space, width=bocal_w, height=bocal_h)
        self._space = space
        self._maxline = self._walls[MAXLINE]
        self._dropzone = DropZone(bocal_body=self._body, width=bocal_w, height=bocal_h)
        self.reset()

    def reset(self):
        # Keep the body position fixed at reference position
        self._body.position = self._position_ref
        self._body.angle = 0
        self._body.velocity = (0, 0)  # Ensure no velocity
        self._body.angular_velocity = 0  # Ensure no rotation

        self._shake = SHAKE_OFF
        self._shake_start_time = None     # t0 for automatic shake 
        self._shake_mouse_target = None   # position of bocal to reach in SHAKE_MOUSE mode

        self._tumble = TUMBLE_OFF
        self._tumble_start_time = None 


    def delete(self):
        for w in self.walls.values():
            w.delete()
        self._space.remove( self._body )


    def to_world(self, bocal_coords):
        return self._body.local_to_world(bocal_coords)

    def to_bocal(self, world_coords):
        return self._body.world_to_local(world_coords)

    @property
    def width(self):
        bot = self._walls[BOTTOM].segment
        return (bot.b - bot.a).length
    
    @property
    def is_tumbling(self):
        return self._tumble != TUMBLE_OFF


    def fruits_sur_maxline(self):
        """ Id des fruits en contact avec maxline
        """
        sqi = self._space.shape_query( self._maxline.segment )
        fruit = [ s.shape.fruit for s in sqi ]
        return fruit


    def step(self, dt):
        self._update_shake(dt)
        self._update_tumble(dt)
        self._update_walls(dt)


    def _update_walls(self, dt):
        """ deplace les murs 
        """
        for wall in self._walls.values():
            local_pos = wall.bocal_position_func(self._width_ref, self._height_ref)
            world_pos = self._body.local_to_world(local_pos)
            wall.move_to(position=world_pos, angle=self._body.angle, dt=dt)


    def shake_auto(self):
        self._shake = SHAKE_AUTO
        self._shake_start_time = utils.now()


    def shake_mouse(self):
        self._shake = SHAKE_MOUSE
        self._shake_mouse_target = self._position_ref


    def shake_stop(self):
        self._shake = SHAKE_STOPPING
        self._shake_start_time = None
        self._shake_mouse_target = None


    def _update_shake(self, dt):
        """ secoue le bocal
        """
        def auto_shake_x(t):
            assert(t >= 0)
            d = SHAKE_ACCEL_DELAY
            f1 = SHAKE_FREQ_MIN
            f2 = SHAKE_FREQ_MAX
            k = (f2-f1)/2
            if(t < SHAKE_ACCEL_DELAY):
                return 2 * math.pi * t * (f1 + k*t/d)
            else:
                return 2 * math.pi * t * (f2 - k*d/t)

        if(self._shake == SHAKE_OFF):
            # Ensure container stays fixed when not shaking
            self._body.velocity = (0, 0)
            return

        # oscillation sinusoidale accelerée
        elif(self._shake == SHAKE_AUTO):
            (x_ref, y_ref) = self._position_ref
            t = utils.now() - self._shake_start_time
            p = (x_ref + SHAKE_AMPLITUDE_X * math.sin(auto_shake_x(t)), y_ref)
            velocity = (p - self._body.position)/dt

        # retour amorti à la position de reference
        elif(self._shake == SHAKE_STOPPING):
            dist = self._position_ref - self._body.position
            if(dt > 0.000001 and dist.length > 0.000001):
                velocity = SHAKE_RETURN_SPEED * dist / dt
            else:
                velocity = pm.Vec2d(0, 0)

            # condition d'arret de l'amorti
            dist_from_position_ref = (self._body.position - self._position_ref)
            if(dist_from_position_ref.length < 1):
                velocity = (0, 0)
                self._body.position = self._position_ref
                self._shake = SHAKE_OFF

        # se dirige vers la position cible du mouseshake
        elif(self._shake == SHAKE_MOUSE):
            dist = self._shake_mouse_target - self._body.position
            velocity = SHAKE_MOUSE_SPEED * dist / dt

        self._body.velocity = velocity


    def tumble_once(self):
        self._tumble = TUMBLE_ONCE
        self._body.angular_velocity =  2 * math.pi * TUMBLE_FREQ


    def _update_tumble(self, dt):
        """ mode machine à laver: rotation du bocal
        """
        if( self._tumble == TUMBLE_OFF):
            return 
        elif( self._tumble == TUMBLE_ONCE):
            if( self._body.angle > 2*math.pi):
                self._body.angle = 0
                self._body.angular_velocity = 0
                self._tumble = TUMBLE_OFF
                self._tumble_start_time = None

    def update(self):
        """ Met à jour les position des objets graphiques depuis la simulation physique
        """
        for w in self._walls.values():
            w.update()


    def on_mouse_motion(self, x, y, dx, dy):
        """ Secoue le bocla en fonction des mouvements de la souris
        """
        if(self._shake==SHAKE_MOUSE):
            dv = pm.Vec2d(dx, dy)/3
            (xt, yt) = self._shake_mouse_target + dv
            (x_ref, y_ref) =  self._position_ref
            xt = min( max(xt, x_ref - SHAKE_AMPLITUDE_X ), x_ref + SHAKE_AMPLITUDE_X)
            yt = min( max(yt, y_ref - SHAKE_AMPLITUDE_Y ), y_ref + SHAKE_AMPLITUDE_Y)
            self._shake_mouse_target = (xt, yt)


    def on_resize(self, center, bocal_w, bocal_h):
        self._position_ref = center
        self._width_ref = bocal_w
        self._height_ref = bocal_h
        self._dropzone.on_resize( bocal_w, bocal_h)
        for wall in self._walls.values():
            wall.on_resize( bocal_w, bocal_h)  # change uniquement la longueur du mur
        if( self._shake == SHAKE_OFF ):
            self.shake_stop()  # pour déplacer lentement le body vers la nouvelle position de ref.


    def drop_point_cursor(self, x_cursor, margin ):
        return self._dropzone.drop_point_cursor(x_cursor, margin=margin/self.width)


    def drop_point_random(self, margin):
        return self._dropzone.drop_point_random(margin / self.width)


