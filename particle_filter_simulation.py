import pygame
import numpy as np
import math
from dataclasses import dataclass
from enum import Enum


# window and grid constants
WINDOW_SIZE = 800
CELL_SIZE = 40  # 20, 40, 80, 100
GRID_SIZE = WINDOW_SIZE // CELL_SIZE
NUM_PARTICLES = 1000
SENSOR_MAX_DISTANCE = 10

# colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
SKY_BLUE = (0, 191, 255)

# movement constants
MOVEMENT_SPEED = 0.2
ROTATION_SPEED = 5


class MovementMode(Enum):
    MANUAL = "Manual Control"
    RANDOM = "Random Movement"


@dataclass
class SimulationConfig:
    """configuration parameters for controlling simulation precision"""
    movement_noise: float = 0.1  # how much noise in movement (higher = less precise)
    rotation_noise: float = 5.0  # how much noise in rotation (degrees)
    sensor_noise: float = 0.5  # how much noise in sensor readings
    resampling_noise: float = 1.0  # standard deviation for measurement likelihood


@dataclass
class SensorReading:
    front: float
    left: float
    right: float
    back: float


class Robot:
    def __init__(self, x, y, orientation, config: SimulationConfig):
        self.x = x
        self.y = y
        self.orientation = orientation
        self.config = config

    def move(self, delta_x, delta_y, delta_orientation, environment_map):
        # add configured noise to movement
        noisy_dx = delta_x + np.random.normal(0, self.config.movement_noise)
        noisy_dy = delta_y + np.random.normal(0, self.config.movement_noise)
        noisy_dorientation = delta_orientation + np.random.normal(0, self.config.rotation_noise)

        # calculate new position
        new_x = self.x + noisy_dx
        new_y = self.y + noisy_dy

        # check if new position would be in an obstacle
        grid_x = int(new_x)
        grid_y = int(new_y)

        if 0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE and environment_map[grid_y][grid_x] == 0:
            self.x = new_x
            self.y = new_y
            self.orientation = (self.orientation + noisy_dorientation) % 360
            return True
        return False

    def sense(self, environment_map):
        readings = SensorReading(
            front=self._get_distance(environment_map, 0),
            left=self._get_distance(environment_map, 90),
            right=self._get_distance(environment_map, 270),
            back=self._get_distance(environment_map, 180)
        )
        return readings

    def _get_distance(self, environment_map, relative_angle):
        angle = math.radians((self.orientation + relative_angle) % 360)
        dx = math.cos(angle)
        dy = math.sin(angle)

        distance = 0
        curr_x, curr_y = self.x, self.y

        while distance < SENSOR_MAX_DISTANCE:
            grid_x = int(curr_x)
            grid_y = int(curr_y)

            if (grid_x < 0 or grid_x >= GRID_SIZE or
                    grid_y < 0 or grid_y >= GRID_SIZE or
                    environment_map[grid_y][grid_x] == 1):
                break

            curr_x += dx
            curr_y += dy
            distance += 1

        # add configured sensor noise
        return distance + np.random.normal(0, self.config.sensor_noise)


class Particle:
    def __init__(self, x, y, orientation, config: SimulationConfig, weight=1.0):
        self.x = x
        self.y = y
        self.orientation = orientation
        self.weight = weight
        self.config = config

    def move(self, delta_x, delta_y, delta_orientation, environment_map):
        # add configured noise to movement
        noisy_dx = delta_x + np.random.normal(0, self.config.movement_noise)
        noisy_dy = delta_y + np.random.normal(0, self.config.movement_noise)
        noisy_dorientation = delta_orientation + np.random.normal(0, self.config.rotation_noise)

        # calculate new position
        new_x = self.x + noisy_dx
        new_y = self.y + noisy_dy

        # check if new position would be in an obstacle
        grid_x = int(new_x)
        grid_y = int(new_y)

        if 0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE and environment_map[grid_y][grid_x] == 0:
            self.x = new_x
            self.y = new_y
            self.orientation = (self.orientation + noisy_dorientation) % 360
            return True
        return False

    def sense(self, environment_map):
        readings = SensorReading(
            front=self._get_distance(environment_map, 0),
            left=self._get_distance(environment_map, 90),
            right=self._get_distance(environment_map, 270),
            back=self._get_distance(environment_map, 180)
        )
        return readings

    def _get_distance(self, environment_map, relative_angle):
        angle = math.radians((self.orientation + relative_angle) % 360)
        dx = math.cos(angle)
        dy = math.sin(angle)

        distance = 0
        curr_x, curr_y = self.x, self.y

        while distance < SENSOR_MAX_DISTANCE:
            grid_x = int(curr_x)
            grid_y = int(curr_y)

            if (grid_x < 0 or grid_x >= GRID_SIZE or
                    grid_y < 0 or grid_y >= GRID_SIZE or
                    environment_map[grid_y][grid_x] == 1):
                break

            curr_x += dx
            curr_y += dy
            distance += 1

        return distance

    def update_weight(self, robot_measurement, environment_map):
        particle_measurement = self.sense(environment_map)

        # calculate likelihood using configured resampling noise
        likelihood = (
                gaussian(robot_measurement.front - particle_measurement.front, 0, self.config.resampling_noise) *
                gaussian(robot_measurement.left - particle_measurement.left, 0, self.config.resampling_noise) *
                gaussian(robot_measurement.right - particle_measurement.right, 0, self.config.resampling_noise) *
                gaussian(robot_measurement.back - particle_measurement.back, 0, self.config.resampling_noise)
        )

        self.weight *= likelihood


def gaussian(x, mu, sigma):
    return math.exp(-((x - mu) ** 2) / (2 * sigma ** 2))


class ParticleFilter:
    def __init__(self, config: SimulationConfig, num_particles: int):
        self.config = config
        self.num_particles = num_particles
        self.particles = []

    def initialize(self, environment_map):
        self.particles = []
        for _ in range(self.num_particles):
            while True:
                x = np.random.uniform(1, GRID_SIZE - 1)
                y = np.random.uniform(1, GRID_SIZE - 1)
                if environment_map[int(y)][int(x)] == 0:
                    self.particles.append(Particle(x, y, np.random.uniform(0, 360), self.config))
                    break

    def update(self, robot_measurement, delta_x, delta_y, delta_orientation, environment_map):
        # move and update weights for all particles
        for particle in self.particles:
            particle.move(delta_x, delta_y, delta_orientation, environment_map)
            particle.update_weight(robot_measurement, environment_map)

        # resample particles
        self.particles = self._resample()

    def _resample(self):
        weights = np.array([p.weight for p in self.particles])
        weights /= np.sum(weights)  # Normalize weights

        indices = np.random.choice(
            range(len(self.particles)),
            size=len(self.particles),
            p=weights
        )

        return [Particle(
            x=self.particles[i].x,
            y=self.particles[i].y,
            orientation=self.particles[i].orientation,
            config=self.config
        ) for i in indices]


def create_random_map():
    # create empty map
    map_data = np.zeros((GRID_SIZE, GRID_SIZE))

    # add random obstacles
    for _ in range(GRID_SIZE * GRID_SIZE // 10):
        x = np.random.randint(0, GRID_SIZE)
        y = np.random.randint(0, GRID_SIZE)
        map_data[y][x] = 1

    # add border walls
    map_data[0, :] = 1
    map_data[-1, :] = 1
    map_data[:, 0] = 1
    map_data[:, -1] = 1

    return map_data


def draw_sensor_lines(screen, robot, sensor_readings):
    robot_x = int(robot.x * CELL_SIZE)
    robot_y = int(robot.y * CELL_SIZE)

    # draw front sensor (red)
    angle = math.radians(robot.orientation)
    end_x = robot_x + sensor_readings.front * CELL_SIZE * math.cos(angle)
    end_y = robot_y + sensor_readings.front * CELL_SIZE * math.sin(angle)
    pygame.draw.line(screen, RED, (robot_x, robot_y), (end_x, end_y), 2)

    # draw left sensor
    angle = math.radians(robot.orientation + 90)
    end_x = robot_x + sensor_readings.left * CELL_SIZE * math.cos(angle)
    end_y = robot_y + sensor_readings.left * CELL_SIZE * math.sin(angle)
    pygame.draw.line(screen, GRAY, (robot_x, robot_y), (end_x, end_y), 2)

    # draw right sensor
    angle = math.radians(robot.orientation - 90)
    end_x = robot_x + sensor_readings.right * CELL_SIZE * math.cos(angle)
    end_y = robot_y + sensor_readings.right * CELL_SIZE * math.sin(angle)
    pygame.draw.line(screen, GRAY, (robot_x, robot_y), (end_x, end_y), 2)

    # draw back sensor
    angle = math.radians(robot.orientation + 180)
    end_x = robot_x + sensor_readings.back * CELL_SIZE * math.cos(angle)
    end_y = robot_y + sensor_readings.back * CELL_SIZE * math.sin(angle)
    pygame.draw.line(screen, GRAY, (robot_x, robot_y), (end_x, end_y), 2)


def calculate_average_position(particles):
    """calculate the average position of all particles"""
    x_sum = sum(p.x for p in particles)
    y_sum = sum(p.y for p in particles)
    count = len(particles)
    return x_sum / count, y_sum / count


def calculate_position_error(robot_x, robot_y, avg_x, avg_y):
    """calculate Euclidean distance between robot and average particle position"""
    return math.sqrt((robot_x - avg_x) ** 2 + (robot_y - avg_y) ** 2)


def draw_error_text(screen, error):
    """draw error value on screen"""
    font = pygame.font.Font(None, 36)
    text = font.render(f"Average Distance between robot and particles: {error:.2f} cells", True, BLACK)
    screen.blit(text, (10, WINDOW_SIZE + 10))


def draw_mode_text(screen, mode):
    """draw current movement mode on screen"""
    font = pygame.font.Font(None, 36)
    mode_text = font.render(f"Mode: {mode.value} (Press M to toggle)", True, BLACK)
    screen.blit(mode_text, (10, WINDOW_SIZE + 10))

    if mode == MovementMode.MANUAL:
        controls_text = font.render("Controls: Arrow keys to move, A/D to rotate", True, BLACK)
        screen.blit(controls_text, (400, WINDOW_SIZE + 10))


def handle_keyboard_input(robot):
    """handle keyboard inputs for manual robot control"""
    keys = pygame.key.get_pressed()
    delta_x = 0
    delta_y = 0
    delta_orientation = 0

    # movement
    if keys[pygame.K_UP]:
        delta_x = MOVEMENT_SPEED * math.cos(math.radians(robot.orientation))
        delta_y = MOVEMENT_SPEED * math.sin(math.radians(robot.orientation))
    if keys[pygame.K_DOWN]:
        delta_x = -MOVEMENT_SPEED * math.cos(math.radians(robot.orientation))
        delta_y = -MOVEMENT_SPEED * math.sin(math.radians(robot.orientation))
    if keys[pygame.K_LEFT]:
        delta_x = MOVEMENT_SPEED * math.cos(math.radians(robot.orientation - 90))
        delta_y = MOVEMENT_SPEED * math.sin(math.radians(robot.orientation - 90))
    if keys[pygame.K_RIGHT]:
        delta_x = MOVEMENT_SPEED * math.cos(math.radians(robot.orientation + 90))
        delta_y = MOVEMENT_SPEED * math.sin(math.radians(robot.orientation + 90))

    # rotation
    if keys[pygame.K_a]:  # rotate left
        delta_orientation = ROTATION_SPEED
    if keys[pygame.K_d]:  # rotate right
        delta_orientation = -ROTATION_SPEED

    return delta_x, delta_y, delta_orientation


def get_random_movement():
    """generate random movement values"""
    delta_x = np.random.normal(0, 0.1)
    delta_y = np.random.normal(0, 0.1)
    delta_orientation = np.random.normal(0, 5)
    return delta_x, delta_y, delta_orientation


def main():
    np.random.seed(1234)
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + 46))
    clock = pygame.time.Clock()

    # create configuration with desired precision
    config = SimulationConfig(
        movement_noise=0.1,  # decrease for more precise movement
        rotation_noise=5.0,  # decrease for more precise rotation
        sensor_noise=0.5,  # decrease for more precise sensors
        resampling_noise=1.0  # decrease for stricter particle resampling
    )

    # initialize environment
    environment_map = create_random_map()

    # initialize robot in free space
    robot_x = robot_y = GRID_SIZE // 2
    while environment_map[int(robot_y)][int(robot_x)] == 1:
        robot_x = np.random.uniform(1, GRID_SIZE - 1)
        robot_y = np.random.uniform(1, GRID_SIZE - 1)

    # initialize robot and particle filter
    robot = Robot(robot_x, robot_y, 0, config)
    particle_filter = ParticleFilter(config, NUM_PARTICLES)
    particle_filter.initialize(environment_map)

    robot_measurement = robot.sense(environment_map)

    movement_mode = MovementMode.MANUAL
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_m:  # Toggle movement mode
                    movement_mode = MovementMode.RANDOM if movement_mode == MovementMode.MANUAL else MovementMode.MANUAL

        # move robot randomly
        if movement_mode == MovementMode.MANUAL:
            delta_x, delta_y, delta_orientation = handle_keyboard_input(robot)
            should_update = delta_x != 0 or delta_y != 0 or delta_orientation != 0
        else:
            delta_x, delta_y, delta_orientation = get_random_movement()
            should_update = True

        # update robot and particle filter only when there's movement
        if should_update:
            robot.move(delta_x, delta_y, delta_orientation, environment_map)
            robot_measurement = robot.sense(environment_map)
            particle_filter.update(robot_measurement, delta_x, delta_y, delta_orientation, environment_map)

        # calculate average position and error
        avg_x, avg_y = calculate_average_position(particle_filter.particles)
        position_error = calculate_position_error(robot.x, robot.y, avg_x, avg_y)

        # draw everything
        screen.fill(WHITE)

        # draw map
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if environment_map[y][x] == 1:
                    pygame.draw.rect(screen, BLACK,
                                     (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

        # draw particles
        for particle in particle_filter.particles:
            x = int(particle.x * CELL_SIZE)
            y = int(particle.y * CELL_SIZE)
            pygame.draw.circle(screen, BLUE, (x, y), 2)

        # draw average position
        avg_pos_x = int(avg_x * CELL_SIZE)
        avg_pos_y = int(avg_y * CELL_SIZE)
        pygame.draw.circle(screen, SKY_BLUE, (avg_pos_x, avg_pos_y), 5)

        # draw robot
        robot_x = int(robot.x * CELL_SIZE)
        robot_y = int(robot.y * CELL_SIZE)
        pygame.draw.circle(screen, RED, (robot_x, robot_y), 5)

        # draw robot's orientation
        end_x = robot_x + 10 * math.cos(math.radians(robot.orientation))
        end_y = robot_y + 10 * math.sin(math.radians(robot.orientation))
        pygame.draw.line(screen, BLUE, (robot_x, robot_y), (end_x, end_y), 2)

        draw_sensor_lines(screen, robot, robot_measurement)

        draw_error_text(screen, position_error)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == '__main__':
    main()
