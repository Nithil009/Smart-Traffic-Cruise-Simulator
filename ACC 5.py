import pygame
import math
import random
from collections import deque

pygame.init()

# --------------------------------------------------
# Display Settings
# --------------------------------------------------
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Two-Way Traffic Simulation (No Overlap)")

FPS = 60

# --------------------------------------------------
# Road and Visual Settings
# --------------------------------------------------
ROAD_TOP = 0
ROAD_BOTTOM = SCREEN_HEIGHT
ROAD_CENTER_X = SCREEN_WIDTH // 2

LANE_WIDTH = 200
LANE_COUNT = 2

# Colors
GRASS_COLOR = (34, 139, 34)
ROAD_COLOR = (50, 50, 50)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Two distance thresholds (tweak as needed):
# These are bounding-box distances, not center-to-center.
SAFE_DISTANCE = 100         # If front car is within this bounding distance, slow down.
DETECTION_DISTANCE = 150    # If front car is within this bounding distance, cone goes red.

# --------------------------------------------------
# Helper Functions
# --------------------------------------------------
def draw_road():
    """
    Draw the road with:
    - Gray rectangle for asphalt.
    - White boundary lines (no yellow center lines).
    """
    SCREEN.fill(GRASS_COLOR)  # Grass background
    
    # Road rectangle
    road_left = ROAD_CENTER_X - (LANE_WIDTH // 2)
    pygame.draw.rect(
        SCREEN,
        ROAD_COLOR,
        (road_left, ROAD_TOP, LANE_WIDTH, ROAD_BOTTOM - ROAD_TOP)
    )
    
    # White boundary lines
    pygame.draw.line(SCREEN, WHITE, (road_left, ROAD_TOP), (road_left, ROAD_BOTTOM), 4)
    pygame.draw.line(
        SCREEN,
        WHITE,
        (road_left + LANE_WIDTH, ROAD_TOP),
        (road_left + LANE_WIDTH, ROAD_BOTTOM),
        4
    )


def draw_trees_and_signs():
    """
    Draw a few static trees and signs for decoration.
    """
    tree_positions = [(200, 100), (150, 300), (220, 500),
                      (SCREEN_WIDTH - 180, 200), (SCREEN_WIDTH - 160, 500)]
    
    for (tx, ty) in tree_positions:
        trunk_color = (139, 69, 19)
        leaves_color = (0, 100, 0)
        trunk_w, trunk_h = 10, 30
        # Trunk
        pygame.draw.rect(SCREEN, trunk_color, (tx, ty, trunk_w, trunk_h))
        # Leaves
        pygame.draw.circle(SCREEN, leaves_color, (tx + trunk_w // 2, ty), 20)

    # Simple sign example
    sign_positions = [(100, 400), (SCREEN_WIDTH - 150, 300)]
    font = pygame.font.SysFont(None, 24)
    for (sx, sy) in sign_positions:
        post_color = (120, 120, 120)
        pygame.draw.rect(SCREEN, post_color, (sx, sy, 5, 40))
        # Sign board
        board_color = (255, 255, 224)
        board_w, board_h = 60, 40
        pygame.draw.rect(
            SCREEN,
            board_color,
            (sx - board_w // 2 + 3, sy - board_h, board_w, board_h)
        )

        # Text on sign
        text_surf = font.render("Limit 80", True, (0, 0, 0))
        SCREEN.blit(text_surf, (sx - board_w // 2 + 5, sy - board_h + 5))


# --------------------------------------------------
# Vehicle Class
# --------------------------------------------------
class Vehicle:
    """
    Represent a top-down view of a car with a simple 'capsule' shape.
    Each vehicle can have an initial speed (which won't increase),
    and it moves either up or down depending on the lane.
    """
    def __init__(self, x, y, color, base_speed, lane_index):
        self.x = x
        self.y = y
        self.color = color
        
        # The car’s desired top speed (no acceleration beyond this).
        self.base_speed = base_speed
        self.speed = base_speed  # current speed can only be <= base_speed

        self.width = 40
        self.height = 60
        self.lane_index = lane_index  # 0 => up, 1 => down

        # Position the car horizontally according to lane index
        self.set_lane_position(lane_index)

    def set_lane_position(self, lane_idx):
        """
        Centers the car in the specified lane horizontally.
        """
        road_left = ROAD_CENTER_X - (LANE_WIDTH // 2)
        single_lane_width = LANE_WIDTH / LANE_COUNT
        lane_center_x = road_left + single_lane_width * (lane_idx + 0.5)
        self.x = lane_center_x

    def update(self, vehicles):
        """
        Move this vehicle either up or down, but first check if there's
        a car in front that's too close in the same lane to avoid overlap.
        """
        front_car, bounding_dist = self.get_front_car_bounding_distance(vehicles)

        if front_car is not None:
            # If bounding distance is smaller than SAFE_DISTANCE, reduce speed
            if bounding_dist < SAFE_DISTANCE:
                # Decelerate or match front car's speed
                self.speed = min(self.speed, front_car.speed)

                # Also ensure we do NOT overlap physically
                # (if bounding_dist < 0, it means we overlapped)
                overlap_amount = SAFE_DISTANCE - bounding_dist
                if overlap_amount > 0:  
                    # We forcibly move this car back a bit to prevent actual overlap
                    if self.lane_index == 0:
                        # Upward lane => move car down
                        self.y += overlap_amount
                    else:
                        # Downward lane => move car up
                        self.y -= overlap_amount
            else:
                # No risk => maintain base speed (no acceleration beyond base).
                self.speed = self.base_speed
        else:
            # No car in front => maintain base speed
            self.speed = self.base_speed

        # Update position based on lane direction
        if self.lane_index == 0:
            # Upward lane (y decreases)
            self.y -= self.speed
            if self.y < -100:
                self.y = SCREEN_HEIGHT + 100
        else:
            # Downward lane (y increases)
            self.y += self.speed
            if self.y > SCREEN_HEIGHT + 100:
                self.y = -100

    def get_front_car_bounding_distance(self, vehicles):
        """
        Returns (closest_front_car, bounding_dist) in the same lane.
        
        'bounding_dist' is the distance from this car’s *front edge* 
        to the front car’s *rear edge*, which better prevents overlap.
        
          - For the upward lane (lane_index=0), front edge is 'y',
            while the front car's rear edge is 'front_car.y + front_car.height'.
          - For the downward lane (lane_index=1), front edge is 'y + height',
            while the front car's rear edge is just 'front_car.y'.

        A positive bounding_dist means there's space; 
        a negative or zero bounding_dist would imply overlap or touching.
        """
        front_car = None
        min_dist = float('inf')

        # Identify this car's front edge
        if self.lane_index == 0:
            # Up-lane => front edge = self.y
            behind_front_edge = self.y
        else:
            # Down-lane => front edge = self.y + self.height
            behind_front_edge = self.y + self.height

        for v in vehicles:
            if v is self:
                continue
            if v.lane_index == self.lane_index:
                # Same lane
                if self.lane_index == 0:
                    # Upward lane => front car has smaller y => v.y < self.y
                    if v.y < self.y:
                        # front car's rear edge = v.y + v.height
                        front_car_rear_edge = v.y + v.height
                        dist = behind_front_edge - front_car_rear_edge

                        if 0 <= dist < min_dist:
                            # 0 <= dist means no overlap yet, and it's the closest so far
                            min_dist = dist
                            front_car = v

                else:
                    # Downward lane => front car has larger y => v.y > self.y
                    if v.y > self.y:
                        # front car's rear edge = v.y
                        front_car_rear_edge = v.y
                        dist = front_car_rear_edge - behind_front_edge

                        if 0 <= dist < min_dist:
                            min_dist = dist
                            front_car = v

        if front_car is not None:
            return (front_car, min_dist)
        return (None, float('inf'))

    def draw(self):
        """
        Draw the vehicle with a capsule shape (rectangle + ellipses).
        """
        rect_x = self.x - self.width / 2
        rect_y = self.y
        rect_w = self.width
        rect_h = self.height

        # Main rectangle
        pygame.draw.rect(SCREEN, self.color, (rect_x, rect_y, rect_w, rect_h))

        # Top ellipse
        pygame.draw.ellipse(
            SCREEN,
            self.color,
            (rect_x, rect_y - rect_w / 2, rect_w, rect_w)
        )
        # Bottom ellipse
        pygame.draw.ellipse(
            SCREEN,
            self.color,
            (rect_x, rect_y + rect_h - rect_w / 2, rect_w, rect_w)
        )

        # Center line detail (for visual)
        pygame.draw.line(
            SCREEN,
            (0, 0, 0),
            (self.x, self.y + 5),
            (self.x, self.y + rect_h - 5),
            2
        )

    def draw_cone(self, vehicles):
        """
        Draw a cone in front of this car:
         - Turn it RED if another car is within DETECTION_DISTANCE (by bounding distance),
         - Otherwise GREEN.
        Also display the bounding distance to that closest front car (if inside cone).
        """
        front_car, bounding_dist = self.get_front_car_bounding_distance(vehicles)

        # Determine whether the cone should be red or green
        cone_color_rgba = (*GREEN, 60)  # default translucent green
        dist_text_value = None

        # If we have a front car and bounding_dist < DETECTION_DISTANCE, turn cone red
        if front_car is not None and bounding_dist < DETECTION_DISTANCE:
            cone_color_rgba = (*RED, 60)
            dist_text_value = bounding_dist

        # Prepare a surface for the cone
        cone_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # For the cone shape, we project forward in the lane direction
        if self.lane_index == 1:
            # Downward lane: cone fans out downward
            cone_start = (self.x, self.y + self.height)
            left_spread = (self.x - 80, self.y + self.height + 250)
            right_spread = (self.x + 80, self.y + self.height + 250)
        else:
            # Upward lane: cone fans out upward
            cone_start = (self.x, self.y)
            left_spread = (self.x - 80, self.y - 250)
            right_spread = (self.x + 80, self.y - 250)

        pygame.draw.polygon(
            cone_surface,
            cone_color_rgba,
            [cone_start, left_spread, right_spread]
        )

        SCREEN.blit(cone_surface, (0, 0))

        # If there's a front car within detection range, display bounding distance
        if dist_text_value is not None:
            font = pygame.font.SysFont(None, 20)
            dist_text = font.render(f"Dist: {dist_text_value:.1f}", True, (0, 0, 0))

            # Put the text near the start of the cone
            if self.lane_index == 1:
                # For downward lane
                text_pos = (cone_start[0] + 5, cone_start[1] + 5)
            else:
                # For upward lane
                text_pos = (cone_start[0] + 5, cone_start[1] - 20)

            SCREEN.blit(dist_text, text_pos)


# --------------------------------------------------
# Main Loop
# --------------------------------------------------
def main():
    clock = pygame.time.Clock()

    # Create vehicles with specified speeds and lanes
    red_car = Vehicle(0, 500, (255, 0, 0), 5, lane_index=1)      # Down
    blue_car = Vehicle(0, 100, (0, 0, 255), 3, lane_index=0)     # Up
    green_car = Vehicle(0, 300, (0, 255, 0), 4, lane_index=0)    # Up
    orange_car = Vehicle(0, 700, (255, 128, 0), 6, lane_index=1) # Down

    vehicles = [red_car, blue_car, green_car, orange_car]

    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update each vehicle
        for v in vehicles:
            v.update(vehicles)

        # Draw scene
        draw_road()
        draw_trees_and_signs()

        # Draw vehicles and cones
        for v in vehicles:
            v.draw()
            v.draw_cone(vehicles)

        # Show the speeds of each car on the screen
        font = pygame.font.SysFont(None, 28)
        y_offset = 10
        for i, v in enumerate(vehicles):
            txt = font.render(f"Car {i+1} Speed: {v.speed:.1f}", True, (0, 0, 0))
            SCREEN.blit(txt, (10, y_offset))
            y_offset += 30

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
