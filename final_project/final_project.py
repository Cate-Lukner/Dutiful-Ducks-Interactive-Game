"""" This is a game full of dutiful ducks.
The player must catch all the lost baby ducks
by climbing trees using the space bar. However,
rogue ducks wander about so the player must do
their best to avoid them or risk a game over.
To get out of the trees, they need to press the
number 1 and use the arrow keys. """

import sys
import random
import math

import astar
import arcade

# --- Constants ---

BABY_DUCKS_COUNT = 10
ROGUE_DUCKS_COUNT = 2

TREE_COUNT = 80

# Sprite Scalings
SPRITE_SCALING_WALL = 0.5
# SPRITE_SCALING_WALL = 1.0
SPRITE_SCALING_TREE = 0.80
SPRITE_SCALING_PLAYER = 0.4
# SPRITE_SCALING_PLAYER = 1.0

SPRITE_SCALING_BABY_DUCK = 0.5
# SPRITE_SCALING_BABY_DUCK = 1.0

# Screen Diminsions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600


VIEWPORT_MARGIN = 80

# Grid size constants
GRID_ROWS = 16
GRID_COLS = 16
GRID_SIZE = 68

# Coordinates for Walls
wall_coordinates = [
    (i, 0) for i in range(GRID_ROWS)
] + [
    (0, j) for j in range(GRID_COLS)
] + [
    (i, GRID_COLS - 1) for i in range(GRID_ROWS)
] + [
    (GRID_ROWS - 1, j) for j in range(GRID_COLS)
]

# Creates coordinates for trees in terms of grid rows/cols
tree_coordinates = [
    (i, j) for j in range(1, GRID_COLS - 1) for i in range(1, GRID_ROWS - 1)
]


def shuffled(seq):
    """ returns a shuffle sequence the same length of 
    the original senquence. """

    return random.sample(seq, len(seq))

# Shuffles the tree coordinates
shuffled_tree_coordinates = shuffled(tree_coordinates)


def get_xy(row, col, size=GRID_SIZE):
    """ Converts row and column to x and y pixels. """
    x = col * size + size // 2
    y = row * size + size // 2
    return x, y

def get_ij(x, y, size=GRID_SIZE):
    """ Converts a pixel x y to a grid row/col. """
    TW, TH = GRID_COLS * size, GRID_ROWS * size
    i = y // size
    j = x // size
    return i, j
 
def get_sprite_ij(sprite):
    """ Gets the grid row/col of the sprite. """
    return get_ij(sprite.center_x, sprite.center_y)


def draw_grid():
    """ Draws grid lines for reference. """
    lines = []
    for i, j in zip(range(GRID_ROWS), range(GRID_COLS)):
        lines.append((i, 0, i, GRID_COLS - 1))
        lines.append((0, j, GRID_ROWS - 1, j))
    hs = GRID_SIZE // 2
    for si, sj, ei, ej in lines:
        x0, y0 = get_xy(si, sj)
        x1, y1 = get_xy(ei, ej)
        
        arcade.draw_line(x0 - hs, y0 - hs, x1 - hs, y1 - hs, (0, 0, 0, 255))

def draw_grass_background():
    """ Draws grass background """

    # Background image by athile on OpenGameArt.org
    texture = arcade.load_texture("images/grass_background.png")
    
    # Loop through and create 20 panels of grass background images
    for i in range(4):
        for j in range(5):
            arcade.draw_texture_rectangle(
                (j * SCREEN_WIDTH), (i * SCREEN_HEIGHT),
                SCREEN_WIDTH, SCREEN_HEIGHT,
                texture 
            )

def highlight_sprite(sprite, color=(255, 255, 255, 50)):
    """ Draws a rectangle over the sprite. """

    arcade.draw_rectangle_filled(
        sprite.center_x, sprite.center_y,
        sprite.width, sprite.height, color,
    )

class GridAStar(astar.AStar):
    def __init__(self, grid):
        self.grid = grid

    def neighbors(self, node):
        i, j = node
        if i != (len(self.grid) - 1) and self.grid[i + 1][j] is not None:
            yield (i + 1, j)
        if j != (len(self.grid[0]) - 1) and self.grid[i][j + 1] is not None:
            yield (i, j + 1)
        if i != 0 and self.grid[i - 1][j] is not None:
            yield (i - 1, j)
        if j != 0 and self.grid[i][j - 1] is not None:
            yield (i, j - 1)

    def distance_between(self, n1, n2):
        return 1

    def heuristic_cost_estimate(self, n1, n2):
        return math.hypot(n2[0] - n1[0], n2[1] - n1[1])

class RogueDuck(arcade.Sprite):
    """ Contains the methods associated with the
    Rogue Duck. """

    def __init__(self, image, scaling):
        """ Constructor function """

        # Calls parent constructor
        super().__init__(image, scaling)

        # Sets a random movement speed and direction
        # for the rogue duck
        self.change_x = random.randrange(-3, 4)
        self.change_y = random.randrange(-3, 4)

        # Just in case both change_x and change_y 
        # are randomly chosen to be zero
        if self.change_x == 0 and self.change_y == 0:
            self.change_x = 1
            self.change_y = -1

    def update(self):
        """ Updates the rogue duck and allows the
        ducks to move within a boundary and bounce off
        the boundary. """

        # Call parent update method
        super().update()

        # Gets the x, y for boundaries
        x_right, y_top = get_xy(GRID_ROWS, GRID_COLS)
        x_left, y_bottom = get_xy(0, 0)

        # Change direction of rogue duck if duck hits boundary
        if self.right >= x_right or self.left <= x_left:
            self.change_x *= -1
        elif self.top >= y_top or self.bottom <= y_bottom:
            self.change_y *= -1

    

class MyGame(arcade.Window):
    """ Represents the main window of the game."""

    def __init__(self):
        """ Initializer """

        # Call the parent class initializer
        super().__init__(
            SCREEN_WIDTH, SCREEN_HEIGHT, 
            "Dutiful Ducks Prototype"
        )

        # Set up player coordinate and speed
        self.player_coordinate = None
        self.player_speed = 10


        # Sprite lists
        self.player_list = None
        self.wall_list = None
        self.baby_duck_list = None
        self.tree_list = None
        self.wall_block_list = None
        self.rogue_duck_list = None
        self.available_spaces_list = None

        self.grid = None
        self.astar = None

        # Set up free space
        self.available_space = False

        # Set up the player
        self.player_sprite = None

        # Set up the bad ducks
        self.rogue_duck_sprite = None

        self.nearest = None

        # Set up attributes associated
        # with trees
        self.trees_in_range = None
        self.picked_tree = None
        self.picked_tree_index = None

        # Set up game states
        self.pick_tree_state = False
        self.in_tree_state = False
        self.picking_free_space = False
        self.game_state = True
        self.win = False

        # Holds "physics engine"
        self.physics_engine = None
        # self.rogue_duck_physics_engine = None

        # Sets inital view to (0, 0)
        self.view_left = 0
        self.view_bottom = 0

        # Sets score to zero
        self.score = 0

        # Initialize game over sprite to
        # appear on the screen
        # All sprite images from kenney.nl
        self.game_over = arcade.Sprite(
            "images/text_gameover.png", 1.5
        )

        # Sound from ZapSplat.com
        self.captured_duck_sound = arcade.load_sound(
            "sounds/duck_sound.mp3"
        )


    def setup(self):
        """
        Creates instances of sprite lists assigned to attributes
        created in constructor method. Also creates instances
        of sprites and adds them to their respective lists. 
        Contains logic to randomly place trees and ducks. 
        """

        # Sprite Lists
        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.baby_duck_list = arcade.SpriteList()
        self.tree_list = arcade.SpriteList()
        self.wall_block_list = arcade.SpriteList()
        self.rogue_duck_list = arcade.SpriteList()
        self.character_sprites_list = arcade.SpriteList()
        self.available_spaces_list = arcade.SpriteList()

        # Reset the score
        self.score = 0

        # Player image from Kenney.nl
        self.player_sprite = arcade.Sprite(
            "images/chick.png", SPRITE_SCALING_PLAYER
        )

        # Adds player to player list
        self.player_list.append(self.player_sprite)
        self.character_sprites_list.append(self.player_sprite)

        # Get list of tree coordinates
        tree_placement = shuffled_tree_coordinates[:TREE_COUNT]
        self.tree_placement = tree_placement

        # Iterate over tree coordinate list and create
        # instances of trees for each coordinate
        for coord in tree_placement:
            tree = arcade.Sprite(
                "images/treeGreen_small.png", SPRITE_SCALING_TREE,
            )

            # Random Placement of trees
            i, j = coord
            x, y = get_xy(i, j)

            tree.center_x = x
            tree.center_y = y

            # Adds trees to wall list and tree_list
            self.wall_list.append(tree)
            self.tree_list.append(tree)

        # Get possible coordinates for player that are
        # not where the trees are
        self.player_coordinate = random.choice(
            list(set(tree_coordinates) - set(tree_placement))
        )
        x, y = get_xy(*self.player_coordinate)
        
        # Set the player coordiantes to random choice
        # of coordinate in the grid
        self.player_sprite.center_x = x
        self.player_sprite.center_y = y

        # --- Wall of ducks boundary placement ---
        for (i, j) in wall_coordinates:
            x, y = get_xy(i, j)
            wall_sprite = arcade.Sprite(
                "images/duck.png", SPRITE_SCALING_WALL
            )
            wall_sprite.center_x = x
            wall_sprite.center_y = y
            self.wall_list.append(wall_sprite)
            self.wall_block_list.append(wall_sprite)

        # Get coordinates of baby ducks from tree coordinates
        duck_placement = random.sample(tree_placement, BABY_DUCKS_COUNT)

        # Place baby ducks randomly with the same
        # coordinates as trees
        for i, j in duck_placement:
            x, y = get_xy(i, j)
            # Image from Kenney.nl
            baby_duck = arcade.Sprite(
                "images/baby_duck.png",
                SPRITE_SCALING_BABY_DUCK,
            )

            baby_duck.center_x = x
            baby_duck.center_y = y
            self.baby_duck_list.append(baby_duck)
        
        # Get possible coordinates for rogue ducks that
        # are not where the player or trees are
        rogue_duck_coords = list(
            set(tree_coordinates) - (
                set(tree_placement) | {self.player_coordinate}
            )
        )
        
        rogue_duck_placement = random.sample(
            rogue_duck_coords, ROGUE_DUCKS_COUNT
        )

        # Image from Kenney.nl

        # Create instances of rogue ducks with
        # random coordiantes
        for i, j in rogue_duck_placement:
            rogue_duck = RogueDuck(
                "images/duck_circle.png",
                SPRITE_SCALING_PLAYER,
            )


            x, y = get_xy(i, j)
            rogue_duck.center_x = x
            rogue_duck.center_y = y

            self.rogue_duck_list.append(rogue_duck)
            self.character_sprites_list.append(rogue_duck)

        # Have the player interact with walls
        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player_sprite, self.wall_list
        )


        # Set up AStar

        self.grid = []
        for i in range(GRID_ROWS):
            self.grid.append([0] * GRID_COLS)
        for i, j in tuple(wall_coordinates) + tuple(tree_placement):
            self.grid[i][j] = None
        self.astar = GridAStar(self.grid)

    def update(self, delta_time):
        """ Contains logic to update sprites and view. """

        # Updates physics engine
        self.physics_engine.update()

        # Update Rogue Ducks
        self.rogue_duck_list.update()

        # Find the closest trees
        self.trees_in_range = [
            t for t in self.tree_list
            if arcade.get_distance_between_sprites(self.player_sprite, t) < 100
        ]

        # --- Manage Scrolling ---

        # Track if we need to change the viewport
        changed = False

        # Scroll left
        left_bndry = self.view_left + VIEWPORT_MARGIN
        if self.player_sprite.left < left_bndry:
            self.view_left -= left_bndry - self.player_sprite.left

            changed = True

        # Scroll right
        right_bndry = self.view_left + SCREEN_WIDTH - VIEWPORT_MARGIN
        if self.player_sprite.right > right_bndry:
            self.view_left += self.player_sprite.right - right_bndry

            changed = True

        # Scroll up
        top_bndry = self.view_bottom + SCREEN_HEIGHT - VIEWPORT_MARGIN

        if self.player_sprite.top > top_bndry:
            self.view_bottom += self.player_sprite.top - top_bndry

            changed = True

        # Scroll down
        bottom_bndry = self.view_bottom + VIEWPORT_MARGIN
        if self.player_sprite.bottom < bottom_bndry:
            self.view_bottom -= bottom_bndry - self.player_sprite.bottom

            changed = True

        self.view_left = int(self.view_left)
        self.view_bottom = int(self.view_bottom)

        if changed:
            arcade.set_viewport(
                self.view_left, 
                SCREEN_WIDTH + self.view_left - 1,
                self.view_bottom,
                SCREEN_HEIGHT + self.view_bottom - 1
            )

        # Checks for collision between player and baby duck
        duck_and_baby_duck_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.baby_duck_list,
        )

        # Kill baby duck sprite if collision with player
        if len(duck_and_baby_duck_hit_list) > 0:
            for baby_duck in duck_and_baby_duck_hit_list:
                baby_duck.kill()
                self.score += 1
                arcade.play_sound(self.captured_duck_sound)


        if self.score == BABY_DUCKS_COUNT:
            self.player_speed = 0
            self.game_state = False
            self.game_over.center_x = self.view_left + 400
            self.game_over.center_y = self.view_bottom + 300
            self.win = True


        # Check if player has collided with rogue duck
        player_rogue_duck_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.rogue_duck_list
        )

        # Kill game if player collided with rogue duck
        if len(player_rogue_duck_hit_list) > 0:
            self.player_speed = 0
            self.game_state = False
            self.game_over.center_x = self.view_left + 400
            self.game_over.center_y = self.view_bottom + 300

            
    def on_draw(self):
        """ Draws Everything """

        arcade.start_render()

        # Draw the background
        draw_grass_background()

        # Draws sprite lists
        self.wall_block_list.draw()
        self.tree_list.draw()
        self.player_list.draw()
        self.baby_duck_list.draw()
        self.rogue_duck_list.draw()

        # Highlight the trees that are within the minimum distance
        if not self.in_tree_state:
            for t in self.trees_in_range:
                highlight_sprite(t)

        if self.picked_tree_index is not None:
            picked_tree = self.trees_in_range[self.picked_tree_index]
            highlight_sprite(picked_tree, (255, 0, 0, 50))

        # Draws score beneath player
        arcade.draw_text(
            f"Score: {self.score}", 
            self.view_left + 10, 
            self.view_bottom + 10, 
            arcade.color.WHITE, 14
        )

        # Draw game over
        if not self.game_state:
            self.game_over.draw()

            # if the player won
            if self.win:
                arcade.draw_text(
                    "You Won!", 
                    self.game_over.center_x - 105, 
                    self.game_over.center_y - 125, 
                    arcade.color.WHITE, 40
                )
            
            # if the player lost
            elif not self.win:
                arcade.draw_text(
                    "You Lost :(", 
                    self.game_over.center_x - 100, 
                    self.game_over.center_y - 125, 
                    arcade.color.WHITE, 40
                )

        # draw the available spaces if the player
        # presses one and is in a tree
        if self.in_tree_state:
            self.available_spaces_list.draw()

        # Draw grid for reference
        # draw_grid()


    def on_key_press(self, key, modifiers):
        """ Called whenever a key is pressed. """

        # Logic for assignment of keys and movement directions
        if not self.pick_tree_state and not self.in_tree_state:
            if key == arcade.key.UP:
                self.player_sprite.change_y = self.player_speed
            elif key == arcade.key.DOWN:
                self.player_sprite.change_y = -self.player_speed
            elif key == arcade.key.LEFT:
                self.player_sprite.change_x = -self.player_speed
            elif key == arcade.key.RIGHT:
                self.player_sprite.change_x = self.player_speed
        elif self.pick_tree_state:
            # Pick a tree
            if self.trees_in_range:
                # There is a tree within range
                self.picked_tree_index = (
                    self.picked_tree_index + 1
                ) % len(self.trees_in_range)
            
        if key == arcade.key.SPACE:
            self.pick_tree_state = True
            if self.trees_in_range:
                self.picked_tree_index = 0
            self.nearest, distance = arcade.get_closest_sprite(
                self.player_sprite, self.wall_list
            )
            if distance < 100:
                self.wall_list.remove(self.nearest)
                tree_collision = True
                self.in_tree_state = True

        if key == arcade.key.KEY_1:

            self.picking_free_space = True

            pi, pj = get_sprite_ij(self.player_sprite)
            possible = []
            for i, j in [(pi + 1, pj), (pi, pj + 1),
                         (pi - 1, pj), (pi, pj - 1)]:
                if not((i, j) in self.tree_placement or
                       (i, j) in wall_coordinates):
                    possible.append((i, j))

            for i, j in possible:
                free_space = arcade.Sprite(
                    "images/chick.png",
                    SPRITE_SCALING_PLAYER
                )
                x, y = get_xy(i, j)
                free_space.center_x = x
                free_space.center_y = y

                self.available_spaces_list.append(free_space)

        # Allow player to use arrow keys if they are picking
        # a free space
        if self.picking_free_space and key == arcade.key.UP:
            self.in_tree_state = False

        elif self.picking_free_space and key == arcade.key.DOWN:
            self.in_tree_state = False

        elif self.picking_free_space and key == arcade.key.LEFT:
            self.in_tree_state = False

        elif self.picking_free_space and key == arcade.key.RIGHT:
            self.in_tree_state = False
            
                    
        
    def on_key_release(self, key, modifiers):
        """ Called when the user releases a key. """

        # logic for stopping player when arrow key is released
        if key == arcade.key.UP or key == arcade.key.DOWN:
            self.player_sprite.change_y = 0
        elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player_sprite.change_x = 0
        
        # Move player into tree when player releases space bar
        if key == arcade.key.SPACE:
            self.pick_tree_state = False
            if self.picked_tree_index is not None:
                picked_tree = self.trees_in_range[self.picked_tree_index]
                self.player_sprite.center_x = picked_tree.center_x
                self.player_sprite.center_y = picked_tree.center_y
                self.in_tree_state = True
                self.picked_tree = picked_tree
                self.picked_tree_index = None
            tree_collision = False
            if not tree_collision:
                self.wall_list.append(self.nearest)

        # Player leaves picking free space
        if key == arcade.key.KEY_1:
            self.picking_free_space = False

            # Make free spaces disappear
            for space in self.available_spaces_list[:]:
                space.kill()
        
           

def main():
    """ Main Function. Creates instance of window class and 
    calls set up function. """

    window = MyGame()
    window.setup()
    arcade.run()

# Call main function
if __name__ == "__main__":
    main()
