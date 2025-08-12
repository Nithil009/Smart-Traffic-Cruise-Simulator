# Adaptive Cruise Control and Traffic Simulation

This project is a simulation of a single-lane traffic system that demonstrates adaptive cruise control using virtual sensors. It’s built with Python and Pygame, and it shows how vehicles can maintain safe distances by calculating distances in software rather than using physical sensors.

In this simulation each vehicle has properties like position, base speed, current speed, and dimensions for collision detection. The virtual sensor works by calculating the distance to the vehicle ahead. If the gap falls below a preset safe threshold, the vehicle slows down; otherwise, it maintains its base speed. A cone is drawn in front of each vehicle to visually represent its “field of awareness.” When another vehicle enters this area, the cone changes color to indicate caution.

Below is the core function that simulates the sensor by checking the distance to the nearest car ahead:

```python
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
    return front_car, min_dist
```

The main loop continuously updates the positions of the vehicles based on these sensor readings, redraws the road and scenery, and updates the display, creating a seamless simulation of traffic flow and adaptive cruise control.

<img width="1600" height="900" alt="image" src="https://github.com/user-attachments/assets/a92a9429-49c0-4cbc-9dc4-253ef7d06ecf" />

<img width="1600" height="900" alt="image" src="https://github.com/user-attachments/assets/715b43a4-162d-4add-b68a-c7617bcfa975" />

<img width="1600" height="900" alt="image" src="https://github.com/user-attachments/assets/a6118339-9a5c-44a3-bb3a-7368b7e9ead2" />
