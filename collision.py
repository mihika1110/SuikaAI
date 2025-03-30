import pyglet as pg
from constants import *
from fruit import nb_fruits


def _is_fruit_shape(shape):
    return shape.collision_type > 0 and shape.collision_type<=nb_fruits()

def _get_fruit(arbiter):
    # Detects the fruit and the maxline in the collision
    if( _is_fruit_shape( arbiter.shapes[0]) ):
        return arbiter.shapes[0].fruit
    elif ( _is_fruit_shape( arbiter.shapes[1])):
        return arbiter.shapes[1].fruit
    else:
        raise RuntimeError( "Collision without fruit")

def _get_fruit_first_drop(arbiter):
    """ Detects the fruit MODE_FIRST_DROP in a collision
    """
    s0 =arbiter.shapes[0]  # Alias
    s1 =arbiter.shapes[1]

    first_fruit = None   # Results
    other_fruit = None
    if( s0.collision_type==COLLISION_TYPE_FIRST_DROP ):
        first_fruit = s0.fruit
        if( _is_fruit_shape(s1) ):
            other_fruit = s1.fruit
    if( s1.collision_type==COLLISION_TYPE_FIRST_DROP ):
        first_fruit = s1.fruit
        if( _is_fruit_shape(s0) ):
            other_fruit = s0.fruit
    if( not first_fruit ):
        raise AssertionError("collision handler called on something other than a fruit in FIRST_DROP mode")
    return (first_fruit, other_fruit)


class CollisionHelper(object):
    """ Contains the callback called by pymunk for each collision 
    and the algorithms for choosing the fruits to merge and create
    """
    def __init__(self, space):
        self.reset()
        self.setup_handlers( space )


    def reset( self ):
         self._collisions_fruits = []
         self._actions = []

    def collision_fruit( self, arbiter ):
        """ Callback for pymunk collision_handler
        """
        s0 = arbiter.shapes[0]
        s1 = arbiter.shapes[1]

        shapes = arbiter.shapes
        assert( len(shapes)==2 ), " WTF ???"
        assert( s0.fruit.kind == s1.fruit.kind )
        self._collisions_fruits.append( (s0.fruit, s1.fruit) )
        return True


    def collision_first_drop( self, arbiter ):
        """ Called when a fruit falls on another for the first time after being introduced into play
        """
        (first_fruit, other_fruit) = _get_fruit_first_drop(arbiter)
        self._actions.append( lambda : first_fruit.normal() )
        # The first collision is also a normal collision
        if( other_fruit and first_fruit.kind==other_fruit.kind ):
            self.collision_fruit(arbiter)
        return True

    def collision_maxline_begin(self, arbiter):
        f = _get_fruit(arbiter)
        # Deferred execution, the action may change in case of collision with another fruit
        self._actions.append( lambda : f.blink( activate=True, delay= BLINK_DELAY ) )
        return False  # Ignores collisions with maxline for physics simulation

    def collision_maxline_separate(self, arbiter):
        f = _get_fruit(arbiter)
        # Deferred execution, the action may change in case of collision or other
        self._actions.append( lambda : f.blink( activate=False ) )
        return False  # Ignores collisions with maxline for physics simulation

    def _collision_sets(self):
        """ Searches for connected components in the collision graph
        The graph is defined by an adjacency list
        """
        if( not self._collisions_fruits ):  # Optimization
            return []

        # Set of balls involved in collisions to be resolved
        fruits = set( [pair[0] for pair in self._collisions_fruits] 
                     +[pair[1] for pair in self._collisions_fruits] )

        # Builds the graph of balls in contact
        g = { f:set() for f in fruits }
        for (a, b) in self._collisions_fruits :
            g[a].add(b)
            g[b].add(a)

        # Searches for connected components in the graph 
        composantes = []
        already_found = set()
        for origine in fruits:
            if origine in already_found:
                continue
            already_found.add(origine)
            composante = {origine}
            suivant = [origine]
            while suivant:
                x = suivant.pop()
                already_found.add(x)
                for y in g[x]:
                    if y not in composante:
                        composante.add(y)
                        suivant.append(y)
            composantes.append(composante)
        return composantes


    def _process_collisions(self, spawn_func, world_to_bocal_func):
        """ Modifies the fruits according to collisions that occurred during pymunk.step()
        """
        # Processes explosions  
        for collision_set in self._collision_sets():
            # List of Fruit from IDs, sorted by altitude
            explose_fruits = sorted( collision_set,  key=lambda f: f.position.y )
            assert len( explose_fruits ) >= 2, "collision à un seul fruit ???"

            # Processes only the 2 lowest fruits in case of multiple collisions
            f0 = explose_fruits[0]
            f1 = explose_fruits[1]
            assert( f0.kind == f1.kind )
            self._actions.append( f0.explose )
            self._actions.append( lambda : f1.merge_to( dest=f0.position ) )

            # Replaces the exploded fruits with a single new larger fruit
            # Copies the info because f0 may be REMOVED when spawn() is called
            kind = min( f0.kind + 1, nb_fruits() )
            bocal_coords = world_to_bocal_func( f0.position )
            spawn_fruit = lambda dt : spawn_func(kind=kind, bocal_coords=bocal_coords)
            pg.clock.schedule_once( spawn_fruit, delay=SPAWN_DELAY )


    def process(self, spawn_func, world_to_bocal_func):
        self._process_collisions(spawn_func, world_to_bocal_func)

        # Executes actions on existing fruits ( explose(), blink(), etc... )
        for action in self._actions:
            action()
        self.reset()


    def setup_handlers(self, space):

        # Collisions between fruits in normal mode
        for kind in range(1, nb_fruits()+1):
            h = space.add_collision_handler(kind, kind)
            h.begin = lambda arbiter, space, data : self.collision_fruit(arbiter)

        # Collisions of FIRST_DROP fruits with normal fruits or the ground
        h = space.add_wildcard_collision_handler( COLLISION_TYPE_FIRST_DROP )
        h.begin = lambda arbiter, space, data: self.collision_first_drop(arbiter)

        # Collisions with maxline
        h = space.add_wildcard_collision_handler( COLLISION_TYPE_MAXLINE )
        h.begin = lambda arbiter, space, data : self.collision_maxline_begin(arbiter)
        h.separate = lambda arbiter, space, data : self.collision_maxline_separate(arbiter)