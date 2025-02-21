import pygame
import math
import random
from collections import deque

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60

ROAD_TOP = 100
ROAD_BOTTOM = HEIGHT - 50
LANE_WIDTH = 200

# Colors
BLUE_CAR_COLOR = (0, 0, 255)
RED_CAR_COLOR = (255, 0, 0)
SAFE_DISTANCE_LINE_COLOR = (0, 255, 0)
UNSAFE_DISTANCE_LINE_COLOR = (255, 0, 0)
ROAD_COLOR = (50, 50, 50)
GRASS_COLOR = (34, 139, 34)

class Vehicle:
    def __init__(self, x, y, color, max_speed):
        self.x = x
        self.y = y
        self.color = color
        self.speed = 0
        self.max_speed = max_speed
        
        # Instead of a rectangle, let's define a polygon (top-down view)
        # We'll store relative points that we draw around (x, y)
        self.width = 40
        self.height = 60  # length
        # Use angle 0 for forward. We can rotate if we want turning in the future.
        self.angle = 0
    
    def update(self):
        self.y += self.speed  # move down the screen

        # Reset position if car reaches bottom (for the blue car, or just demonstration)
        if self.y > HEIGHT + self.height:
            self.y = -self.height

    def draw(self, screen):
        """
        Draw a simple top-down car as a polygon:
            - A main rectangle with a slight trapezoid shape for interest
        """
        # Car center = (self.x, self.y)
        # We'll define corners relative to center, then rotate (if needed).
        # But for simplicity, no rotation if angle=0.
        top_left     = (self.x - self.width/2, self.y)
        top_right    = (self.x + self.width/2, self.y)
        bottom_right = (self.x + self.width/2.5, self.y + self.height)
        bottom_left  = (self.x - self.width/2.5, self.y + self.height)

        pygame.draw.polygon(screen, self.color, [top_left, top_right, bottom_right, bottom_left])
        
        # Optional: add some small “headlights” or “tail-lights” if you like
        headlight_radius = 4
        pygame.draw.circle(screen, (255, 255, 224), (int(self.x - self.width/4), int(self.y + 5)), headlight_radius)
        pygame.draw.circle(screen, (255, 255, 224), (int(self.x + self.width/4), int(self.y + 5)), headlight_radius)


class SensorSystem:
    """
    Measures distance from the ego vehicle (red car) to a target vehicle (blue car).
    Includes methods for LIDAR and camera with different noise levels.
    """
    def __init__(self, ego_vehicle, target_vehicle, safe_distance=100):
        self.ego_vehicle = ego_vehicle
        self.target_vehicle = target_vehicle
        self.safe_distance = safe_distance  # "ideal" safe distance in pixels
    
    def get_lidar_reading(self):
        distance = abs(self.target_vehicle.y - self.ego_vehicle.y)
        noise = random.uniform(-2, 2)
        return max(0, distance + noise)

    def get_camera_reading(self):
        distance = abs(self.target_vehicle.y - self.ego_vehicle.y)
        noise = random.uniform(-5, 5)
        return max(0, distance + noise)

    def visualize_sensors(self, screen):
        """
        - Draw a cone-shaped sensor arc in front of the ego vehicle.
        - Draw a direct line between the vehicles, color-coded by safe/unsafe distance.
        """
        ego = self.ego_vehicle
        target = self.target_vehicle

        # The direct line from red to blue car
        distance = self.get_lidar_reading()  # or average
        if distance >= self.safe_distance:
            color = SAFE_DISTANCE_LINE_COLOR
        else:
            color = UNSAFE_DISTANCE_LINE_COLOR

        pygame.draw.line(screen, color,
                         (ego.x, ego.y + ego.height / 2),
                         (target.x, target.y),
                         2)

        # Draw a cone (wedge) in front of the red car
        # We'll just do a wide triangle
        # Starting at the bottom center of the ego car
        cone_start = (ego.x, ego.y + ego.height)
        left_spread = (ego.x - 60, ego.y + ego.height + 200)
        right_spread = (ego.x + 60, ego.y + ego.height + 200)
        
        # Make the cone semi-transparent
        cone_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.polygon(cone_surface, (255, 0, 0, 50), [cone_start, left_spread, right_spread])
        screen.blit(cone_surface, (0, 0))


class ACCController:
    """
    Adaptive Cruise Control logic. 
    The red car tries to maintain a safe distance and does not collide.
    """
    def __init__(self, sensor_system):
        self.sensor_system = sensor_system
        self.desired_speed = 50
        self.min_safe_distance = 80

    def calculate_safe_distance(self, current_speed):
        # Basic formula: safe distance grows with speed
        return self.min_safe_distance + (current_speed / 10)

    def control_speed(self, current_distance):
        """
        - If too close, decelerate
        - If too far, accelerate to desired speed
        - Otherwise, hold
        """
        ego_vehicle = self.sensor_system.ego_vehicle
        safe_distance = self.calculate_safe_distance(ego_vehicle.speed)

        # Make sure we never exceed max speed
        if ego_vehicle.speed > ego_vehicle.max_speed:
            ego_vehicle.speed = ego_vehicle.max_speed
        
        if current_distance < safe_distance:
            # Decelerate
            reduction = (safe_distance - current_distance) / safe_distance * 20
            new_speed = max(0, ego_vehicle.speed - reduction)
            return new_speed
        elif current_distance > safe_distance + 20:
            # Accelerate
            new_speed = min(self.desired_speed, ego_vehicle.speed + 2)
            return new_speed
        
        # If we're within a "comfortable" band, hold speed
        return ego_vehicle.speed


def draw_road_and_environment(screen):
    # Fill background with grass
    screen.fill(GRASS_COLOR)
    
    # Draw road rectangle
    pygame.draw.rect(screen, ROAD_COLOR, (WIDTH//2 - LANE_WIDTH//2, ROAD_TOP,
                                          LANE_WIDTH, ROAD_BOTTOM - ROAD_TOP))
    
    # Draw lane lines (center dashed line, for example)
    line_color = (255, 255, 255)
    dash_height = 20
    gap = 20
    x_center = WIDTH//2
    y = ROAD_TOP
    while y < ROAD_BOTTOM:
        pygame.draw.line(screen, line_color, (x_center, y), (x_center, y + dash_height), 2)
        y += dash_height + gap

    # Road boundaries
    pygame.draw.line(screen, (200, 200, 200),
                     (WIDTH//2 - LANE_WIDTH//2, ROAD_TOP),
                     (WIDTH//2 - LANE_WIDTH//2, ROAD_BOTTOM), 4)
    pygame.draw.line(screen, (200, 200, 200),
                     (WIDTH//2 + LANE_WIDTH//2, ROAD_TOP),
                     (WIDTH//2 + LANE_WIDTH//2, ROAD_BOTTOM), 4)


def draw_distance_plot(screen, distances_deque):
    plot_width, plot_height = 200, 100
    plot_x, plot_y = WIDTH - plot_width - 10, 10
    margin = 5

    pygame.draw.rect(screen, (240, 240, 240), (plot_x, plot_y, plot_width, plot_height))
    pygame.draw.rect(screen, (0, 0, 0), (plot_x, plot_y, plot_width, plot_height), 2)

    # If we have fewer than 2 points, there's no line to draw
    if len(distances_deque) < 2:
        # Optionally display the single distance if you want
        if len(distances_deque) == 1:
            font = pygame.font.Font(None, 20)
            text = font.render(f"Distance: {distances_deque[-1]:.1f}", True, (0, 0, 0))
            screen.blit(text, (plot_x + 5, plot_y + 5))
        return

    max_dist = max(distances_deque)
    min_dist = min(distances_deque)
    dist_range = max_dist - min_dist if max_dist != min_dist else 1

    points = []
    for i, dist in enumerate(distances_deque):
        px = plot_x + margin + (i / (len(distances_deque) - 1)) * (plot_width - 2*margin)
        scaled = (dist - min_dist) / dist_range
        py = plot_y + (plot_height - margin) - scaled * (plot_height - 2*margin)
        points.append((px, py))

    if len(points) > 1:
        pygame.draw.lines(screen, (0, 0, 255), False, points, 2)

    # Display the latest distance as text
    font = pygame.font.Font(None, 20)
    text = font.render(f"Distance: {distances_deque[-1]:.1f}", True, (0, 0, 0))
    screen.blit(text, (plot_x + 5, plot_y + 5))



def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Enhanced ACC Simulation")
    clock = pygame.time.Clock()
    
    # Create vehicles
    # Place them on the "road" center
    road_center = WIDTH // 2
    blue_car = Vehicle(road_center, -80, BLUE_CAR_COLOR, max_speed=3)
    red_car = Vehicle(road_center, -200, RED_CAR_COLOR, max_speed=5)
    
    # Initialize sensor & ACC
    sensor_system = SensorSystem(red_car, blue_car, safe_distance=100)
    acc_controller = ACCController(sensor_system)
    
    # Keep track of distance over time for real-time plot
    distance_history = deque(maxlen=100)  # store last 100 frames

    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Distance measurements
        lidar_distance = sensor_system.get_lidar_reading()
        camera_distance = sensor_system.get_camera_reading()
        avg_distance = (lidar_distance + camera_distance) / 2
        
        # Update red car's speed via ACC
        red_car.speed = acc_controller.control_speed(avg_distance)
        
        # Keep the blue car at constant speed
        blue_car.speed = 3
        
        # Update positions
        red_car.update()
        blue_car.update()
        
        # Draw environment
        draw_road_and_environment(screen)
        
        # Draw vehicles
        blue_car.draw(screen)
        red_car.draw(screen)
        
        # Visualize sensors (cone + distance line)
        sensor_system.visualize_sensors(screen)

        # Update distance history for plotting
        distance_history.append(avg_distance)
        
        # Draw a small real-time plot in top-right
        draw_distance_plot(screen, distance_history)
        
        # Speed displays
        font = pygame.font.Font(None, 28)
        blue_speed_text = font.render(f'Blue Car Speed: {blue_car.speed:.1f}', True, (0, 0, 0))
        red_speed_text = font.render(f'Red Car Speed : {red_car.speed:.1f}', True, (0, 0, 0))
        screen.blit(blue_speed_text, (10, 10))
        screen.blit(red_speed_text, (10, 40))
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()
