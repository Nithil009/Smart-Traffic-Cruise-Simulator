import pygame
import random

pygame.init()

# --------------------------------------------------
# Display Settings
# --------------------------------------------------
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Single Lane Traffic Simulation")

FPS = 60

# --------------------------------------------------
# Road and Visual Settings
# --------------------------------------------------
ROAD_LEFT = 0
ROAD_RIGHT = SCREEN_WIDTH
ROAD_CENTER_Y = SCREEN_HEIGHT // 2

# Increase the road width
LANE_WIDTH = 300
ROAD_TOP = ROAD_CENTER_Y - LANE_WIDTH // 2
ROAD_BOTTOM = ROAD_CENTER_Y + LANE_WIDTH // 2
SAFE_EDGE_DISTANCE = 20  # Minimum distance from the road edges

# Colors
GRASS_COLOR = (34, 139, 34)
ROAD_COLOR = (50, 50, 50)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Two distance thresholds (tweak as needed):
SAFE_DISTANCE = 100         # If front car is within this bounding distance, slow down.
DETECTION_DISTANCE = 150    # If front car is within this bounding distance, cone goes red.
OVERTAKE_DISTANCE = 200      # Distance to check for overtaking

# --------------------------------------------------
# Helper Functions
# --------------------------------------------------
def draw_road():
    SCREEN.fill(GRASS_COLOR)  # Grass background
    pygame.draw.rect(
        SCREEN,
        ROAD_COLOR,
        (ROAD_LEFT, ROAD_CENTER_Y - LANE_WIDTH // 2, ROAD_RIGHT, LANE_WIDTH)
    )
    pygame.draw.line(SCREEN, WHITE, (ROAD_LEFT, ROAD_TOP), (ROAD_RIGHT, ROAD_TOP), 4)
    pygame.draw.line(SCREEN, WHITE, (ROAD_LEFT, ROAD_BOTTOM), (ROAD_RIGHT, ROAD_BOTTOM), 4)

def draw_trees():
    # Draw trees on the sides of the road
    tree_positions = [(100, 100), (200, 100), (100, 500),
                      (SCREEN_WIDTH - 100, 100), (SCREEN_WIDTH - 200, 100), (SCREEN_WIDTH - 100, 500)]
    
    for (tx, ty) in tree_positions:
        trunk_color = (139, 69, 19)
        leaves_color = (0, 100, 0)
        trunk_w, trunk_h = 10, 30
        # Draw trunk
        pygame.draw.rect(SCREEN, trunk_color, (tx, ty, trunk_w, trunk_h))
        # Draw leaves
        pygame.draw.circle(SCREEN, leaves_color, (tx + trunk_w // 2, ty), 20)

# --------------------------------------------------
# Vehicle Class
# --------------------------------------------------
class Vehicle:
    def __init__(self, x, color, base_speed, name):
        self.x = x
        self.y = ROAD_CENTER_Y
        self.color = color
        self.base_speed = base_speed
        self.speed = base_speed
        self.width = 60
        self.height = 30
        self.name = name  # Add name attribute
        self.is_overtaking = False  # Track if the vehicle is overtaking

    def update(self, vehicles):
        front_car, bounding_dist = self.get_front_car_bounding_distance(vehicles)

        if self.name == "Blue Car":  # Only Car 2 (Blue Car) will attempt to overtake
            if front_car is not None:
                if bounding_dist < SAFE_DISTANCE:
                    # Prevent overlap by stopping at the safe distance
                    self.x = front_car.x - self.width - SAFE_DISTANCE
                    self.speed = 0  # Stop if too close
                elif bounding_dist < DETECTION_DISTANCE:
                    self.speed = self.base_speed * 0.5  # Slow down if within detection distance
                else:
                    self.speed = self.base_speed

                # Check for overtaking
                if self.can_overtake(vehicles):
                    self.is_overtaking = True
                    self.overtake()
                else:
                    self.is_overtaking = False
            else:
                self.speed = self.base_speed
                self.is_overtaking = False

        else:  # For Car 1 and Car 3
            if front_car is not None:
                if bounding_dist < SAFE_DISTANCE:
                    self.x = front_car.x - self.width - SAFE_DISTANCE
                    self.speed = 0  # Stop if too close
                else:
                    self.speed = self.base_speed

            # Car 3 accelerates if there is space
            if self.name == "Green Car":
                if front_car is None or (front_car.x - self.x > 150):  # Check if there's enough space
                    self.speed = self.base_speed + 1  # Accelerate

        # Move to the right (increasing x)
        self.x += self.speed
        if self.x > SCREEN_WIDTH + 100:
            self.x = -100

        # Keep the vehicle within the road boundaries
        self.y = max(ROAD_TOP + SAFE_EDGE_DISTANCE, min(self.y, ROAD_BOTTOM - SAFE_EDGE_DISTANCE))

    def can_overtake(self, vehicles):
        # Check if there's enough space to overtake
        for v in vehicles:
            if v is self:
                continue
            if v.x > self.x and v.x < self.x + OVERTAKE_DISTANCE:
                return False  # Not enough space to overtake
        return True  # Safe to overtake

    def overtake(self):
        # Move diagonally upward while overtaking
        self.x += 5  # Move forward
        self.y -= 1  # Move upward to simulate diagonal movement

        # Ensure the vehicle does not go out of bounds
        if self.y < ROAD_TOP + SAFE_EDGE_DISTANCE:
            self.y = ROAD_TOP + SAFE_EDGE_DISTANCE

        # After overtaking, move diagonally down to return to the lane
        if self.x > 600:  # Assuming the overtaking is done after reaching a certain x position
            self.y += 1  # Move downward to return to the lane

    def get_front_car_bounding_distance(self, vehicles):
        front_car = None
        min_dist = float('inf')
        behind_front_edge = self.x + self.width

        for v in vehicles:
            if v is self:
                continue
            if v.x > self.x:
                dist = v.x - behind_front_edge
                if 0 <= dist < min_dist:
                    min_dist = dist
                    front_car = v

        if front_car is not None:
            return (front_car, min_dist)
        return (None, float('inf'))

    def draw(self):
        # Draw a more car-like shape
        rect_x = self.x
        rect_y = self.y - self.height / 2
        pygame.draw.rect(SCREEN, self.color, (rect_x, rect_y, self.width, self.height))
        pygame.draw.rect(SCREEN, (0, 0, 0), (rect_x + 5, rect_y + 5, self.width - 10, self.height - 10))  # Inner rectangle for detail

        # Draw the name of the vehicle
        font = pygame.font.SysFont(None, 24)
        name_text = font.render(self.name, True, (0, 0, 0))
        SCREEN.blit(name_text, (self.x + 5, self.y - self.height / 2 + 5))

    def draw_cone(self, vehicles):
        front_car, bounding_dist = self.get_front_car_bounding_distance(vehicles)

        cone_color_rgba = (*GREEN, 60)
        dist_text_value = None

        if front_car is not None and bounding_dist < DETECTION_DISTANCE:
            cone_color_rgba = (*RED, 60)
            dist_text_value = bounding_dist

        cone_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        cone_start = (self.x + self.width, self.y)
        left_spread = (self.x + self.width + 250, self.y - 80)
        right_spread = (self.x + self.width + 250, self.y + 80)

        pygame.draw.polygon(cone_surface, cone_color_rgba, [cone_start, left_spread, right_spread])
        SCREEN.blit(cone_surface, (0, 0))

        if dist_text_value is not None:
            font = pygame.font.SysFont(None, 20)
            dist_text = font.render(f"Dist: {dist_text_value:.1f}", True, (0, 0, 0))
            text_pos = (cone_start[0] + 5, cone_start[1] + 5)
            SCREEN.blit(dist_text, text_pos)

# --------------------------------------------------
# Main Loop
# --------------------------------------------------
def main():
    clock = pygame.time.Clock()

    # Create three vehicles with specified starting x-positions, colors, speeds, and names.
    red_car = Vehicle(100, (255, 0, 0), 5, "Red Car")      # Car 1
    blue_car = Vehicle(400, (0, 0, 255), 3, "Blue Car")    # Car 2 (Overtaking)
    green_car = Vehicle(700, (0, 255, 0), 4, "Green Car")  # Car 3

    vehicles = [red_car, blue_car, green_car]

    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update each vehicle
        for v in vehicles:
            v.update(vehicles)

        # Draw scene elements
        draw_road()
        draw_trees()

        # Draw vehicles and their cones
        for v in vehicles:
            v.draw()
            v.draw_cone(vehicles)

        # Display the speeds of each car on the screen
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