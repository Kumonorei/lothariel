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

############################
# Imports
############################

# import the libtcod library
import libtcodpy as libtcod

# import math
import math

# import wordwrap
import textwrap

###########################
# Global Values 
########################### 

# global values
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

# map size
MAP_WIDTH = 80
MAP_HEIGHT = 43

# GUI status bar things

BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1

INVENTORY_WIDTH = 50 

# room generator
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 25

# FOV globals
FOV_ALGO = libtcod.FOV_RESTRICTIVE
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

# potion strength
HEAL_AMOUNT = 8

# monster constants
MAX_ROOM_MONSTERS = 3

# item constants
MAX_ROOM_ITEMS = 1

# map color definitions
color_dark_wall = libtcod.Color(76, 26, 128)
color_light_wall = libtcod.Color(153, 51, 255)
color_dark_ground = libtcod.Color(92, 122, 153) 
color_light_ground = libtcod.Color(153, 204, 255)

################################
# Classes
################################

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
    def __init__(self, x, y, char, name, color, blocks=False, fighter=None, ai=None, item=None):
        self.name = name
        self.blocks = blocks
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        
        self.item = item
        if self.item:
            self.item.owner = self
        
        self.fighter = fighter
        if self.fighter:
            self.fighter.owner = self
            
        self.ai = ai
        if self.ai:
            self.ai.owner = self
        
    # moves the object by the given amount
    def move(self, dx, dy):
        if not is_blocked(self.x + dx, self.y + dy):
            self.x += dx
            self.y += dy
            
    # move towards a target
    def move_towards(self, target_x, target_y):
        # vector from this object to the target, and distance
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        
        # normalize it to length 1 (preserving direction), then round it and
        # convert to int so the movement is restricted to the map grid
        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        self.move(dx, dy)
        
    # find distance
    def distance_to(self, other):
        # return the distance to another object
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)
    
    # set the color and draw the character representing the object on screen
    def draw(self):
        if libtcod.map_is_in_fov(fov_map, self.x, self.y):
            libtcod.console_set_default_foreground(con, self.color)
            libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)
        
    # erase the character representing this object
    def clear(self):
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)

    # move to the start of the object list, forcing it to be drawn first (below other stuff)
    def send_to_back(self):
        global objects
        objects.remove(self)
        objects.insert(0, self)
        
# fighter class
class Fighter:
    # combat related properties and methods 
    def __init__(self, hp, defense, power, death_function=None):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.death_function = death_function
        
    def take_damage(self, damage):
        # apply damage if possible
        if damage > 0:
            self.hp -= damage
            if self.hp <= 0:
               function = self.death_function
               if function is not None:
                   function(self.owner)
            
    # attack target
    def attack(self, target):
        # a simple formula for attack damage
        damage = self.power - target.fighter.defense
        
        if damage > 0:
            # target takes damage
            message(
                self.owner.name.capitalize() + ' attacks ' 
                + target.name + ' for ' + str(damage) + ' hit points.')
            target.fighter.take_damage(damage)
        else:
            message(
                self.owner.name.capitalize() + ' attacks '
                + target.name + ' but it is ineffective.')

    def heal(self, amount):
        # heal by the given amount, without going over the max
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp
            
# basic monster ai
class BasicMonster:
    def take_turn(self):
        # monster takes it's turn. if you can see if, it can see you.
        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
        
            # move towards the player
            if monster.distance_to(player) >= 2:
                monster.move_towards(player.x, player.y)
                
            # within attack range
            elif player.fighter.hp > 0:
                monster.fighter.attack(player)
                
# item
class Item:
    def __init__(self, use_function=None):
        self.use_function = use_function
    def use(self):
        # call the use function if defined
        if self.use_function is None:
            message('The ' + self.owner.name + ' cannot be used.')
        else:
            if self.use_function() != 'cancelled':
                inventory.remove(self.owner) # destroy if used, unless cancelled
                
    def pick_up(self):
        # add to player's inventory and remove from the map
        if len(inventory) >= 26:
            message('Your inventory is full, cannot pick up ' + self.owner.name + '.', libtcod.blue)
        else:
            inventory.append(self.owner)
            objects.remove(self.owner)
            message('You picked up a ' + self.owner.name + '!', libtcod.green)
            
###################################
# Functions
###################################

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

# heal the player
def cast_heal():
    if player.fighter.hp == player.fighter.max_hp:
        message('Your health is full.', libtcod.red)
        return 'cancelled'
        
    message('Your wounds are feeling better!', libtcod.light_violet)
    player.fighter.heal(HEAL_AMOUNT)

# full heal    
def max_heal():
    if player.fighter.hp == player.fighter.max_hp:
        message('Your health is full.', libtcod.red)
        return 'cancelled'
    
    message('Your wounds are healed!', libtcod.violet)
    player.fighter.hp = player.fighter.max_hp

# attack that will damage all enemies in radius of 2 from player    
def cast_lightning():
    for object in objects:
        if object.fighter and not object == player and libtcod.map_is_in_fov(fov_map, object.x, object.y):
            dist = player.distance_to(object)
            if dist <= 2:
                object.fighter.take_damage(8)
                message('A large blast of lightnint damages nearby creatures!')
                
    
        
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
        x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
        y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)
        
        if not is_blocked(x, y):
            if libtcod.random_get_int(0, 0, 100) < 80: # 80% chance of this
                # create a rat
                fighter_component = Fighter(hp=10, defense=0, power=3, death_function=monster_death)
                ai_component = BasicMonster()
                
                monster = Object(x, y, 'r', 'rat', libtcod.light_sepia,
                    blocks=True, fighter=fighter_component, ai=ai_component)
            else:
                # create a radioactive rat
                fighter_component = Fighter(hp=15, defense=1, power=5, death_function=monster_death)
                ai_component = BasicMonster()
                
                monster = Object(x, y, 'R', 'radioactive rat', libtcod.desaturated_green,
                    blocks=True, fighter=fighter_component, ai=ai_component)
            
            objects.append(monster)
            
    # choose a random number of items up to the max
    num_items = libtcod.random_get_int(0, 0, MAX_ROOM_ITEMS)
    
    for i in range(num_items):
        # choose a random spot for the items
        x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
        y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)
        
        if not is_blocked(x, y):
            dice = libtcod.random_get_int(0, 0, 100)
            if dice < 70:
                # create a regular heal potion (70% chance)
                item_component = Item(use_function=cast_heal)
                item = Object(x, y, '!', 'healing potion', libtcod.violet, item=item_component)
            
            elif dice < 80:
                # create a full heal potion (10% chance)
                item_component = Item(use_function=max_heal)
                item = Object(x, y, '!', 'full heal', libtcod.red, item=item_component)
                
            else:
                # create a lightning blast scroll (10% chance)
                item_component = Item(use_function=cast_lightning)
                item = Object(x, y, '?', 'scroll of Lightning Blast', libtcod.white, item=item_component)
                
            
            objects.append(item)
            item.send_to_back() # items should appear below monsters and stuff

# status bar
def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
    bar_width = int(float(value) / maximum * total_width)
    
    # render the background first
    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)
    
    # render the bar on top
    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)
        
    # text containing useful stuff and things
    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER,
        name + ': ' + str(value) + '/' + str(maximum))

def get_names_under_mouse():
    global mouse
    
    # return a string with the names of all objects under the mouse
    (x, y) = (mouse.cx, mouse.cy)
    
    # create a list with the names of objects at the mouse's coordinates and in FOV
    names = [obj.name for obj in objects
        if obj.x == x and obj.y == y and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]
        
    names = ', '.join(names) # join the names, and separate with commas
    return names.capitalize()
        
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
                        libtcod.console_set_char_background(
                            con, x, y, color_dark_wall, libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_char_background(
                            con, x, y, color_dark_ground, libtcod.BKGND_SET)
            else:
                if wall:
                    libtcod.console_set_char_background(
                        con, x, y, color_light_wall,libtcod.BKGND_SET)
                else:
                    libtcod.console_set_char_background(
                        con, x, y, color_light_ground, libtcod.BKGND_SET)
                map[x][y].explored = True
    
    # draw all objects in the object list 
    for object in objects:
        if object != player:
            object.draw()
    player.draw()
                
    libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)    

    # render status bar thing 
    
    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)
    
            
    # print the messages, one line at a time
    y = 1
    for (line, color) in game_msgs:
        libtcod.console_set_default_foreground(panel, color)
        libtcod.console_print_ex(panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
        y += 1
    
    # show the player's health bar in the gui
    
    render_bar(1, 3, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp,
        libtcod.light_red, libtcod.darker_red)
                
    # display names of objects under the mouse
    libtcod.console_set_default_foreground(panel, libtcod.light_gray)
    libtcod.console_print_ex(
        panel, 1, 1, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())
    
    # blit to the root console
    
    libtcod.console_blit(panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)       

# message log
def message(new_msg, color = libtcod.white):
    # split into multiple lines if required
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

    for line in new_msg_lines:
        # if the buffer is full, remove the oldest message to make room for the newest
        if len(game_msgs) == MSG_HEIGHT:
            del game_msgs[0]
            
        # add the new line as a tuple, with text and color
        game_msgs.append( (line, color) )

def player_move_or_attack(dx, dy):
    global fov_recompute
    
    # co-ordinates the player is moving to or attacking
    x = player.x + dx
    y = player.y + dy
    
    # check for attackable object there
    target = None
    for object in objects:
        if object.fighter and object.x == x and object.y == y:
            target = object
            break
            
    # attack if target is found, or else move 
    if target is not None:
        player.fighter.attack(target)
    else:
        player.move(dx, dy)
        fov_recompute = True

# input handling
def handle_keys():
    global fov_recompute
    global keys
        
    # Alt + Enter : toggle fullscreen
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
    
    # Esc : exit game    
    elif key.vk == libtcod.KEY_ESCAPE:
        return 'exit' 
    
    if game_state == 'playing':
        # movement keys
        if key.vk == libtcod.KEY_KP8:
            player_move_or_attack(0, -1)
        
        elif key.vk == libtcod.KEY_KP2:
            player_move_or_attack(0, 1)
        
        elif key.vk == libtcod.KEY_KP4:
            player_move_or_attack(-1, 0)
        
        elif key.vk == libtcod.KEY_KP6:
            player_move_or_attack(1, 0)
        
        elif key.vk == libtcod.KEY_KP1:
            player_move_or_attack(-1, 1)
        
        elif key.vk == libtcod.KEY_KP3:
            player_move_or_attack(1, 1)
        
        elif key.vk == libtcod.KEY_KP7:
            player_move_or_attack(-1, -1)
        
        elif key.vk == libtcod.KEY_KP9:
            player_move_or_attack(1, -1)
            
        else:
            # test for other input
            key_char = chr(key.c)
            
            if key_char == 'g':
                # pick up (Get) item
                for object in objects:
                    if object.x == player.x and object.y == player.y and object.item:
                        object.item.pick_up()
                        break
                        
            if key_char == 'i':
                # show the inventory
                chosen_item = inventory_menu(
                    'Press the key next to an item to use it, or any other to cancel.\n')
                if chosen_item is not None:
                    chosen_item.use()
                        
            return 'didnt-take-turn'
            
# deth n stuff
def player_death(player):
    # ends game
    global game_state
    message('Bye world!', libtcod.red)
    game_state = 'dead'
    
    # change player into a corpse for teh lulz
    player.char = '%'
    player.color = libtcod.dark_red

def monster_death(monster):
    # transforms monster into a corpse that lies around but otherwise doesn't bother anyone
    message(monster.name.capitalize() + ' is dead!', libtcod.orange)
    monster.char = '%'
    monster.color = libtcod.dark_red
    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.name = monster.name + ' corpse'
    monster.send_to_back()

# menu 
9
def menu(header, options, width):
    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options')
    # calculate total height for the header (after auto-wrap) and one line per option
    header_height = libtcod.console_get_height_rect(
        con, 0, 0, width, SCREEN_HEIGHT, header)
    height = len(options) + header_height
    # create a console off screen that represents the menu's window
    window = libtcod.console_new(width, height)
    # print the header, wrap if required
    libtcod.console_set_default_foreground(window, libtcod.white)
    libtcod.console_print_rect_ex(
        window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)
    # print all the options
    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
        y += 1
        letter_index += 1
    # blit the contents of the window to the root console
    x = SCREEN_WIDTH/2 - width/2
    y = SCREEN_HEIGHT/2 - height/2
    libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)
    # present the root console to the player and wit for a key press
    libtcod.console_flush()
    key = libtcod.console_wait_for_keypress(True)
    # convert the ASCII code to an index - if it corresponds to an option then return it
    index = key.c - ord('a')
    if index >= 0 and index < len(options): return index
    return None
    
# inventory menu
def inventory_menu(header):
    if len(inventory) == 0:
        options = ['Inventory is empty.']
    else:
        options = [item.name for item in inventory]
        
    index = menu(header, options, INVENTORY_WIDTH)
    
    if index is None or len(inventory) == 0: return None
    return inventory[index].item
    
###############################
# Initialization and main loop
###############################        
        
# set up console
libtcod.console_set_custom_font(
    'terminal12x12_gs_ro.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW)
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'Lands of Lothariel', False)
libtcod.sys_set_fps(LIMIT_FPS)
con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

# player init
fighter_component = Fighter(hp=30, defense=2, power=5, death_function=player_death)
player = Object(0, 0, '@', 'player', libtcod.white, blocks=True, fighter=fighter_component)

# list of objects in game
objects = [player]

# player's inventory
inventory = []

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

# list of messages in the game
game_msgs = []

# welcome text
message(
    'You stumble into the sewers beneath the fortress of Lothariel.'
    ' Who knows what awaits? You feel uneasy...', libtcod.red)

# controls
mouse = libtcod.Mouse()
key = libtcod.Key()

# main loop
while not libtcod.console_is_window_closed():
    
    libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,key,mouse)
    
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
            if object.ai:
                object.ai.take_turn()

