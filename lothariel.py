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
    def __init__(self, x, y, char, color):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        
    # moves the object by the given amount
    def move(self, dx, dy):
        if not map[self.x + dx][self.y + dy].blocked:
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
                if wall:
                    libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET)
                else:
                    libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)
            else:
                if wall:
                    libtcod.console_set_char_background(con, x, y, color_light_wall,libtcod.BKGND_SET)
                else:
                    libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET)
    
    # draw all objects in the object list 
    for object in objects:
        object.draw()
                
    libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)            
        
# player init
player = Object(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, '@', libtcod.white)

# npc init
npc = Object(SCREEN_WIDTH/2 - 5, SCREEN_HEIGHT/2, '@', libtcod.yellow)

# list of objects in game
objects = [player, npc]

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
        return True 
            
    # movement keys
    if libtcod.console_is_key_pressed(libtcod.KEY_KP8):
        player.move(0, -1)
        fov_recompute = True
        
    elif libtcod.console_is_key_pressed(libtcod.KEY_KP2):
        player.move(0, 1)
        fov_recompute = True
        
    elif libtcod.console_is_key_pressed(libtcod.KEY_KP4):
        player.move(-1, 0)
        fov_recompute = True
        
    elif libtcod.console_is_key_pressed(libtcod.KEY_KP6):
        player.move(1, 0)
        fov_recompute = True
        
    elif libtcod.console_is_key_pressed(libtcod.KEY_KP1):
        player.move(-1, 1)
        fov_recompute = True
        
    elif libtcod.console_is_key_pressed(libtcod.KEY_KP3):
        player.move(1, 1)
        fov_recompute = True
        
    elif libtcod.console_is_key_pressed(libtcod.KEY_KP7):
        player.move(-1, -1)
        fov_recompute = True
        
    elif libtcod.console_is_key_pressed(libtcod.KEY_KP9):
        player.move(1, -1)
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

# main loop
while not libtcod.console_is_window_closed():
    
    render_all()
    
    libtcod.console_flush()
    
    # clear objects old position
    for object in objects:
        object.clear()
    
    # handle keys and exit game if requested
    exit = handle_keys()
    if exit:
        break    
