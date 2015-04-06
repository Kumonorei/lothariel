#!python2

######################
#                    #
# LANDS OF LOTHARIEL #
#                    #
######################


# version 0.01a
# Author: Scott Macleod
#
# A roguelike based on the python/libtcod tutorial 
#


# import the libtcod library
import libtcodpy as libtcod

# constants 

# global values
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

# map size
MAP_WIDTH = 80
MAP_HEIGHT = 45

# room generator
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 25

# FOV globals
FOV_ALGO = 0
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

# monster constants
MAX_ROOM_MONSTERS = 3

# map color definitions
color_dark_wall = libtcod.Color(76, 26, 128)
color_light_wall = libtcod.Color(153, 51, 255)
color_dark_ground = libtcod.Color(92, 122, 153) 
color_light_ground = libtcod.Color(153, 204, 255)

# map tile setup
class Tile:
    # a tile of the map and it's associated properties
    def __init__(self, blocked, block_sight = None):
        self.blocked = blocked
        self.explored = False
    
        # by default, if a tile is blocked, it also blocks sight
        if block_sight is None: block_sight = blocked
        self.block_sight = block_sight

# room setup
class Rect:
    # a rectangle on the map, for making a room
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
    
    def center(self):
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return (center_x, center_y)

    def intersect(self, other):
        #returns true if this rectangle intersects with another one
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)
    
# object setup
class Object:
    # this is a generic object, represented with a character
    def __init__(self, x, y, char, name, color, blocks=False):
        self.name = name
        self.blocks = blocks
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        
    # moves the object by the given amount
    def move(self, dx, dy):
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
    
    # set the color and draw the character representing the object on screen
    def draw(self):
        if libtcod.map_is_in_fov(fov_map, self.x, self.y):
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)
        
    # erase the character representing this object
    def clear(self):
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

# test for blocks
def is_blocked(x, y):
    # test the map tile
    if map[x][y].blocked:
        return True
        
    # test for blocking objects
    for object in objects:
        if object.blocks and object.x == x and object.y == y:
            return True
            
    return False

        
# map init
def create_room(room):
    global map
    # go through the tiles in a rectangle and make them passable
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            map[x][y].blocked = False
            map[x][y].block_sight = False
        
# tunnel builder
def create_h_tunnel(x1, x2, y):
    global map
    for x in range(min(x1, x2), max(x1, x2) +1):
        map[x][y].blocked = False
        map[x][y].block_sight = False
    
def create_v_tunnel(y1, y2, x):
    global map
    for y in range(min(y1, y2), max(y1, y2) +1):
        map[x][y].blocked = False
        map[x][y].block_sight = False
        
def make_map():
    global map, player
    
    # fill map with blocked tiles
    map = [[Tile(True)
        for y in range(MAP_HEIGHT) ]
            for x in range(MAP_WIDTH) ]
            
    rooms = []
    num_rooms = 0
    
    for r in range(MAX_ROOMS):
        # random width and height
        w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        # random position without leaving boundary of map
        x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
        y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)
    
        new_room = Rect(x, y, w, h)
    
        #run through other rooms to check for overlaps
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break
            
        if not failed:
            # draw the room
            create_room(new_room)
            
            # add objects to the room
            place_objects(new_room)
        
            # get the center coordinates
            (new_x, new_y) = new_room.center()
        
            if num_rooms == 0:
                # set starting point in the first room
                player.x = new_x
                player.y = new_y
          
            else:
                # for all rooms after the first, make a tunnel from the previous room
                # using the center coordinates of the previous room
                (prev_x, prev_y) = rooms[num_rooms-1].center()
        
                # flip a coin
                if libtcod.random_get_int(0, 0, 1) == 1:
                    # horizontal first, vertical second
                    create_h_tunnel(prev_x, new_x, prev_y)
                    create_v_tunnel(prev_y, new_y, new_x)
                
                else:
                    # vertical first, horizontal second
                    create_v_tunnel(prev_y, new_y, prev_x)
                    create_h_tunnel(prev_x, new_x, new_y)
           
            # append the new room to the list
            rooms.append(new_room)
            num_rooms += 1

# object placement
def place_objects(room):
    # choose a random number of monsters up to the max
    num_monsters = libtcod.random_get_int(0, 0, MAX_ROOM_MONSTERS)
    
    for i in range(num_monsters):
        # choose a random spot for the monster
        x = libtcod.random_get_int(0, room.x1, room.x2)
        y = libtcod.random_get_int(0, room.y1, room.y2)
        
        if not is_blocked(x, y):        
            if libtcod.random_get_int(0, 0, 100) < 80: # 80% chance of this
                monster = Object(x, y, 'r', 'rat', libtcod.light_sepia, blocks=True)
            else:
                monster = Object(x, y, 'R', 'radioactive rat', libtcod.desaturated_green, blocks=True)
            
            objects.append(monster)
        
# render function
def render_all():
    
    global fov_map, color_dark_wall, color_light_wall
    global color_dark_ground, color_light_ground
    global fov_recompute
       
    # fov 
    if fov_recompute:
        # recompute fov if required
        fov_recompute = False
        libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)
        
    # draw the map
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            visible = libtcod.map_is_in_fov(fov_map, x, y)
            wall = map[x][y].block_sight
            if not visible:
                # prevent player from seeing tiles that haven't previously been uncovered
                if map[x][y].explored:
                    if wall:
                        libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)
            else:
                if wall:
                    libtcod.console_set_char_background(con, x, y, color_light_wall,libtcod.BKGND_SET)
                else:
                    libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET)
                map[x][y].explored = True
    
    # draw all objects in the object list 
    for object in objects:
        object.draw()
                
    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)            
        
# player init
player = Object(0, 0, '@', 'player', libtcod.white, blocks=True)


# list of objects in game
objects = [player]

# input handling
def handle_keys():
    global fov_recompute
    
    # global commands
    key = libtcod.console_wait_for_keypress(True)
    
    # Alt + Enter : toggle fullscreen
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
    
    # Esc : exit game    
    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit' 
    
    if game_state == 'playing':
        # movement keys
        if libtcod.console_is_key_pressed(libtcod.KEY_KP8):
            player_move_or_attack(0, -1)
        
        elif libtcod.console_is_key_pressed(libtcod.KEY_KP2):
            player_move_or_attack(0, 1)
        
        elif libtcod.console_is_key_pressed(libtcod.KEY_KP4):
            player_move_or_attack(-1, 0)
        
        elif libtcod.console_is_key_pressed(libtcod.KEY_KP6):
            player_move_or_attack(1, 0)
        
        elif libtcod.console_is_key_pressed(libtcod.KEY_KP1):
            player_move_or_attack(-1, 1)
        
        elif libtcod.console_is_key_pressed(libtcod.KEY_KP3):
            player_move_or_attack(1, 1)
        
        elif libtcod.console_is_key_pressed(libtcod.KEY_KP7):
            player_move_or_attack(-1, -1)
        
        elif libtcod.console_is_key_pressed(libtcod.KEY_KP9):
            player_move_or_attack(1, -1)
            
        else:
            return 'didnt-take-turn'
   
def player_move_or_attack(dx, dy):
    global fov_recompute
    
    # co-ordinates the player is moving to or attacking
    x = player.x + dx
    y = player.y + dy
    
    # check for attackable object there
    target = None
    for object in objects:
        if object.x == x and object.y == y:
            target = object
            break
            
    # attack if target is found, or else move 
    if target is not None:
        print 'The ' + target.name + ' shrugs off your pathetic attack!'
    else:
        player.move(dx, dy)
        fov_recompute = True
   
# set up console
libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'Lands of Lothariel', False)
con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

# gen map
make_map()

# field of view
fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
for y in range(MAP_HEIGHT):
    for x in range(MAP_WIDTH):
        libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)


fov_recompute = True

game_state = 'playing'
player_action = None

# main loop
while not libtcod.console_is_window_closed():
    
    render_all()
    
    libtcod.console_flush()
    
    # clear objects old position
    for object in objects:
        object.clear()
    
    # handle keys and exit game if requested
    player_action = handle_keys()
    if player_action == 'exit':
        break

    # monsters turn
    if game_state == 'playing' and player_action != 'didnt-take-turn':
        for object in objects:
            if object != player:
                print 'The ' + object.name + ' squeaks!'