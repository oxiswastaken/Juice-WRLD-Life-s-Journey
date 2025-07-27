import pygame
import random
import time
import os
import math
import sys

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Function to get resource path for both development and exe
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# Get screen dimensions for fullscreen
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h
FPS = 144

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (64, 64, 64)
GOLD = (255, 215, 0)
AZURE = (0, 127, 255)
LIME = (0, 255, 127)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Juice WRLD: Life's Journey")
        self.clock = pygame.time.Clock()
        
        # Camera/viewport settings
        self.camera_x = 0
        self.world_to_screen_scale = min(SCREEN_WIDTH, SCREEN_HEIGHT) // 15  # Adaptive scaling for different screen sizes
        
        # Load assets
        self.load_assets()
        
        # Game state
        self.reset_game_state()
        
        # Timing
        self.last_spawn_time = time.time()
        self.last_lifeline_spawn_time = time.time()
        
        # Music state tracking
        self.music_initialized = False
        
    def load_assets(self):
        """Load all game assets with fallbacks"""
        # Load background music - only once during initialization
        self.background_music = None
        try:
            music_path = resource_path('assets/sounds/Afterlife.mp3')
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)  # Loop indefinitely
                self.music_initialized = True
                print("Afterlife.mp3 loaded successfully and playing")
            else:
                print(f"Afterlife.mp3 not found at {music_path}")
        except Exception as e:
            print(f"Failed to load Afterlife.mp3: {e}")
        
        # Load textures with better scaling
        self.bg_texture = self.load_texture('assets/textures/bg.jpg', SCREEN_WIDTH, SCREEN_HEIGHT)
        self.juice_texture = self.load_texture('assets/textures/juice.png', None, None)  # Keep original size for scaling
        self.tiles_texture = self.load_texture('assets/textures/tiles.png', None, None)  # Keep original size for scaling
        self.pills_texture = self.load_texture('assets/textures/pills.png', None, None)  # Keep original size for scaling
        self.lifeline_texture = self.load_texture('assets/textures/999lifeline.png', None, None)  # Keep original size for scaling
        
        # Load font
        try:
            font_path = resource_path('assets/fonts/akira.otf')
            if os.path.exists(font_path):
                self.font_large = pygame.font.Font(font_path, 32)
                self.font_medium = pygame.font.Font(font_path, 24)
                self.font_small = pygame.font.Font(font_path, 18)
                self.font_huge = pygame.font.Font(font_path, 48)
                print("Custom font loaded successfully")
            else:
                raise Exception(f"Font not found at {font_path}")
        except Exception as e:
            print(f"Custom font not found, using default: {e}")
            self.font_large = pygame.font.Font(None, 32)
            self.font_medium = pygame.font.Font(None, 24)
            self.font_small = pygame.font.Font(None, 18)
            self.font_huge = pygame.font.Font(None, 48)
    
    def load_texture(self, relative_path, width=None, height=None):
        """Load and scale texture with fallback"""
        try:
            full_path = resource_path(relative_path)
            if os.path.exists(full_path):
                image = pygame.image.load(full_path).convert_alpha()
                if width and height:
                    image = pygame.transform.scale(image, (width, height))
                print(f"Texture loaded successfully: {relative_path}")
                return image
            else:
                raise Exception(f"Texture file not found: {full_path}")
        except Exception as e:
            print(f"Failed to load texture {relative_path}: {e}")
            # Create fallback colored rectangle
            if width and height:
                surface = pygame.Surface((width, height))
                if 'bg.jpg' in relative_path:
                    surface.fill(LIGHT_GRAY)
                elif 'juice.png' in relative_path:
                    surface.fill(CYAN)
                elif 'tiles.png' in relative_path:
                    surface.fill(GRAY)
                elif 'pills.png' in relative_path:
                    surface.fill(RED)
                elif '999lifeline.png' in relative_path:
                    surface.fill(GREEN)
                return surface
            return None
    
    def reset_game_state(self):
        """Reset all game state variables"""
        # Player state - moved lower to better utilize screen space
        self.player_x = -5
        self.player_y = -6.0  # Lowered from -4.0
        self.velocity = 0
        self.is_jumping = False
        self.player_rotation = 0
        
        # Game variables
        self.obstacles = []
        self.obstacle_data = []
        self.lifelines = []
        self.lifeline_data = []
        self.score = 0
        self.lives = 5
        self.difficulty_level = 1
        self.game_running = True
        self.game_over_screen = False
        self.game_paused = False
        self.invulnerable = False
        self.invulnerable_timer = 0
        self.show_999_forever = False
        
        # Physics constants - Chrome Dino style physics
        self.gravity = 0.015  # Slightly stronger gravity for snappier feel
        self.jump_force = 0.45  # Higher jump force for better control at higher speeds
        self.max_jump_height = 0.2  # Adjusted for new ground level
        self.air_control = 0.9  # Better air control for precision
        self.invulnerable_duration = 1.5  # Shorter invulnerability for faster pace
        
        # Difficulty system - Chrome Dino inspired speeds
        self.base_speed = 0.12  # Increased from 0.05 for faster base speed
        self.speed = self.base_speed
        self.base_spawn_min = 1.0  # Reduced spawn times for more action
        self.base_spawn_max = 2.0  # Reduced spawn times for more action
        self.base_lifeline_spawn_min = 6.0  # More frequent lifelines due to faster pace
        self.base_lifeline_spawn_max = 10.0  # More frequent lifelines due to faster pace
        self.max_difficulty_level = 15  # More difficulty levels for longer progression
        
        # Ground tiles for scrolling - positioned much lower to fill bottom space
        self.ground_tiles = []
        tile_width = 4
        num_tiles = 20  # Extended coverage
        for i in range(num_tiles):
            tile_x = i * tile_width - (num_tiles * tile_width / 2) + 2
            self.ground_tiles.append({'x': tile_x, 'y': -8.0})  # Lowered significantly from -5.5
    
    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates"""
        screen_x = (world_x - self.camera_x) * self.world_to_screen_scale + SCREEN_WIDTH // 2
        screen_y = SCREEN_HEIGHT // 2 - world_y * self.world_to_screen_scale
        return int(screen_x), int(screen_y)
    
    def get_difficulty_multiplier(self):
        """Calculate difficulty multiplier based on current level"""
        return min(self.difficulty_level / self.max_difficulty_level, 1.0)
    
    def get_current_speed(self):
        """Get current game speed based on difficulty - Chrome Dino style acceleration"""
        multiplier = self.get_difficulty_multiplier()
        # More aggressive speed scaling like Chrome Dino
        return self.base_speed * (1 + multiplier * 4)  # Speed can reach 5x base speed
    
    def get_spawn_timing(self):
        """Get current obstacle spawn timing based on difficulty - faster spawning"""
        multiplier = self.get_difficulty_multiplier()
        # More aggressive spawn timing like Chrome Dino
        min_time = self.base_spawn_min * (1 - multiplier * 0.7)  # Gets much faster
        max_time = self.base_spawn_max * (1 - multiplier * 0.7)  # Gets much faster
        return max(0.4, min_time), max(0.8, max_time)  # Minimum spawn times for intense gameplay
    
    def get_lifeline_spawn_timing(self):
        """Get current lifeline spawn timing based on difficulty"""
        multiplier = self.get_difficulty_multiplier()
        min_time = self.base_lifeline_spawn_min * (1 - multiplier * 0.3)
        max_time = self.base_lifeline_spawn_max * (1 - multiplier * 0.3)
        return max(5.0, min_time), max(8.0, max_time)
    
    def get_obstacle_pattern(self):
        """Get obstacle pattern based on difficulty"""
        if self.difficulty_level >= 9:
            return random.choice(['single_ground', 'single_air', 'gap_vertical', 'gap_horizontal', 'triple'])
        elif self.difficulty_level >= 7:
            return random.choice(['single_ground', 'single_air', 'gap_vertical', 'double_stack', 'triple'])
        elif self.difficulty_level >= 5:
            return random.choice(['single_ground', 'single_air', 'gap_vertical', 'double_stack'])
        elif self.difficulty_level >= 3:
            return random.choice(['single_ground', 'single_air', 'double_stack'])
        else:
            return random.choice(['single_ground', 'single_air'])
    
    def update_difficulty(self):
        """Update difficulty level based on score - faster progression like Chrome Dino"""
        # Increase difficulty every 10 points for faster progression
        new_level = min(self.max_difficulty_level, (self.score // 10) + 1)
        if new_level != self.difficulty_level:
            self.difficulty_level = new_level
            self.speed = self.get_current_speed()
    
    def create_pill_obstacle(self, height='ground'):
        """Create a new pill obstacle at specified height - adjusted for new ground level"""
        if height == 'ground':
            base_y = -5.5  # Lowered from -3.5
        elif height == 'low_air':
            base_y = -4.5  # Lowered from -2.5
        elif height == 'mid_air':
            base_y = -3.5  # Lowered from -1.5
        elif height == 'high_air':
            base_y = -2.5  # Lowered from -0.5
        elif height == 'sky':
            base_y = -1.5  # Lowered from 0.5
        else:
            base_y = height
        
        obstacle = {
            'x': 25,  # Spawn much further right to hide spawning (increased from 15)
            'y': base_y,
            'width': 1.5,  # Increased size to match original game
            'height': 1.5
        }
        
        # Store animation data
        multiplier = self.get_difficulty_multiplier()
        animation_speed = random.uniform(1.5, 2.5) * (1 + multiplier * 0.5)
        
        data = {
            'base_y': base_y,
            'animation_offset': random.uniform(0, 6.28),
            'animation_speed': animation_speed
        }
        
        return obstacle, data
    
    def create_obstacle_pattern(self, pattern_type):
        """Create obstacles based on pattern type"""
        obstacles_created = []
        data_created = []
        
        if pattern_type == 'single_ground':
            obs, data = self.create_pill_obstacle('ground')
            obstacles_created.append(obs)
            data_created.append(data)
            
        elif pattern_type == 'single_air':
            height = random.choice(['low_air', 'mid_air', 'high_air'])
            obs, data = self.create_pill_obstacle(height)
            obstacles_created.append(obs)
            data_created.append(data)
            
        elif pattern_type == 'double_stack':
            heights = [random.uniform(-5.5, -4.5), random.uniform(-3.5, -2.5)]  # Adjusted heights
            for height in heights:
                obs, data = self.create_pill_obstacle(height)
                obstacles_created.append(obs)
                data_created.append(data)
        
        elif pattern_type == 'gap_vertical':
            gap_size = random.uniform(2.5, 3.2)
            gap_center = random.uniform(-4.0, -2.5)  # Adjusted center
            
            bottom_height = gap_center - gap_size/2
            if bottom_height > -6.5:  # Adjusted boundary
                obs, data = self.create_pill_obstacle(bottom_height)
                obstacles_created.append(obs)
                data_created.append(data)
            
            top_height = gap_center + gap_size/2
            if top_height < -0.5:  # Adjusted boundary
                obs, data = self.create_pill_obstacle(top_height)
                obstacles_created.append(obs)
                data_created.append(data)
                
        elif pattern_type == 'gap_horizontal':
            obs1, data1 = self.create_pill_obstacle(random.choice(['ground', 'low_air', 'mid_air']))
            obstacles_created.append(obs1)
            data_created.append(data1)
            
            obs2, data2 = self.create_pill_obstacle(random.choice(['low_air', 'mid_air', 'high_air']))
            obs2['x'] += random.uniform(2.0, 3.0)
            obstacles_created.append(obs2)
            data_created.append(data2)
            
        elif pattern_type == 'triple':
            heights = ['ground', 'mid_air', 'high_air']
            random.shuffle(heights)
            
            for i, height in enumerate(heights[:3]):
                obs, data = self.create_pill_obstacle(height)
                obs['x'] += i * 1.8
                obstacles_created.append(obs)
                data_created.append(data)
        
        return obstacles_created, data_created
    
    def create_lifeline(self):
        """Create a new lifeline item - adjusted for new ground level"""
        max_attempts = 10
        base_y = 0
        
        for attempt in range(max_attempts):
            potential_y = random.uniform(-5.0, -3.0)  # Lowered from (-3.0, -1.0)
            safe_position = True
            
            for i, obs in enumerate(self.obstacles):
                if obs['x'] > 23 and obs['x'] < 27:  # Adjusted for new spawn position (increased from 13-17)
                    obs_y = obs['y']
                    if i < len(self.obstacle_data):
                        obs_y = self.obstacle_data[i]['base_y']
                    
                    if abs(potential_y - obs_y) < 1.5:
                        safe_position = False
                        break
            
            if safe_position:
                base_y = potential_y
                break
        else:
            base_y = -2.8  # Lowered from -0.8
        
        lifeline = {
            'x': 25,  # Spawn much further right to hide spawning (increased from 15)
            'y': base_y,
            'width': 1.5,  # Adjusted to be similar size to pills
            'height': 1.5
        }
        
        data = {
            'base_y': base_y,
            'animation_offset': random.uniform(0, 6.28),
            'animation_speed': random.uniform(1.5, 3.0),
            'pulse_offset': random.uniform(0, 6.28)
        }
        
        return lifeline, data
    
    def collect_lifeline(self, lifeline_index):
        """Handle lifeline collection"""
        self.lives += 1
        
        # Remove the collected lifeline
        if lifeline_index < len(self.lifelines):
            self.lifelines.pop(lifeline_index)
            if lifeline_index < len(self.lifeline_data):
                self.lifeline_data.pop(lifeline_index)
    
    def lose_life(self):
        """Handle losing a life"""
        self.lives -= 1
        
        if self.lives <= 0:
            self.game_running = False
            self.game_over_screen = True
        else:
            self.invulnerable = True
            self.invulnerable_timer = self.invulnerable_duration
    
    def update(self, dt):
        """Update game state"""
        if not self.game_running or self.game_paused:
            return
        
        # Ensure music is playing continuously (but don't restart it)
        if self.music_initialized and not pygame.mixer.music.get_busy():
            try:
                music_path = resource_path('assets/sounds/Afterlife.mp3')
                if os.path.exists(music_path):
                    pygame.mixer.music.load(music_path)
                    pygame.mixer.music.play(-1)
            except:
                pass
        
        # Handle invulnerability timer
        if self.invulnerable:
            self.invulnerable_timer -= dt
            if self.invulnerable_timer <= 0:
                self.invulnerable = False
        
        # Apply gravity
        self.velocity -= self.gravity
        self.player_y += self.velocity
        
        # Clamp player to floor - adjusted for new ground level
        if self.player_y <= -6.0:  # Lowered from -4.0
            self.player_y = -6.0
            self.velocity = 0
            self.is_jumping = False
        
        # Update player rotation
        self.player_rotation = 10 if self.is_jumping else 0
        
        # Move ground tiles
        for tile in self.ground_tiles:
            tile['x'] -= self.speed
            if tile['x'] < -30:  # Extended reset position
                tile['x'] += len(self.ground_tiles) * 4
        
        # Update obstacles
        obstacles_to_remove = []
        for i, obs in enumerate(self.obstacles):
            obs['x'] -= self.speed
            
            # Animate up-down movement
            if i < len(self.obstacle_data):
                data = self.obstacle_data[i]
                data['animation_offset'] += data['animation_speed'] * 0.02
                float_amount = math.sin(data['animation_offset']) * 0.3
                obs['y'] = data['base_y'] + float_amount
            
            # Check collision using proper size comparison
            if (abs(self.player_x - obs['x']) < 1.2 and 
                abs(self.player_y - obs['y']) < 1.2 and 
                not self.invulnerable):
                self.lose_life()
                break
            
            # Remove off-screen obstacles (much further left to hide despawning)
            if obs['x'] < -25:  # Extended despawn distance to hide removal (increased from -15)
                obstacles_to_remove.append(i)
                self.score += 1
                self.update_difficulty()
                
                if self.score >= 999:
                    self.show_999_forever = True
        
        # Remove obstacles
        for i in reversed(obstacles_to_remove):
            if i < len(self.obstacles):
                self.obstacles.pop(i)
                if i < len(self.obstacle_data):
                    self.obstacle_data.pop(i)
        
        # Update lifelines
        lifelines_to_remove = []
        for i, lifeline in enumerate(self.lifelines):
            lifeline['x'] -= self.speed
            
            # Animate floating and pulsing
            if i < len(self.lifeline_data):
                data = self.lifeline_data[i]
                data['animation_offset'] += data['animation_speed'] * 0.02
                data['pulse_offset'] += 0.05
                
                float_amount = math.sin(data['animation_offset']) * 0.4
                lifeline['y'] = data['base_y'] + float_amount
                
                pulse_scale = 1.0 + math.sin(data['pulse_offset']) * 0.2
                lifeline['width'] = 1.2 * pulse_scale
                lifeline['height'] = 1.2 * pulse_scale
            
            # Check collision for lifeline collection with proper size
            if (abs(self.player_x - lifeline['x']) < 1.3 and 
                abs(self.player_y - lifeline['y']) < 1.3):
                self.collect_lifeline(i)
                break
            
            # Remove off-screen lifelines (much further left to hide despawning)
            if lifeline['x'] < -25:  # Extended despawn distance to hide removal (increased from -15)
                lifelines_to_remove.append(i)
        
        # Remove lifelines
        for i in reversed(lifelines_to_remove):
            if i < len(self.lifelines):
                self.lifelines.pop(i)
                if i < len(self.lifeline_data):
                    self.lifeline_data.pop(i)
        
        # Spawn obstacles
        now = time.time()
        spawn_min, spawn_max = self.get_spawn_timing()
        
        if now - self.last_spawn_time > random.uniform(spawn_min, spawn_max):
            pattern_type = self.get_obstacle_pattern()
            new_obstacles, new_data = self.create_obstacle_pattern(pattern_type)
            self.obstacles.extend(new_obstacles)
            self.obstacle_data.extend(new_data)
            self.last_spawn_time = now
        
        # Spawn lifelines
        lifeline_min, lifeline_max = self.get_lifeline_spawn_timing()
        
        if now - self.last_lifeline_spawn_time > random.uniform(lifeline_min, lifeline_max):
            if random.random() < 0.5:
                new_lifeline, new_data = self.create_lifeline()
                self.lifelines.append(new_lifeline)
                self.lifeline_data.append(new_data)
                self.last_lifeline_spawn_time = now
    
    def toggle_pause(self):
        """Toggle game pause state"""
        self.game_paused = not self.game_paused
        
        # Pause/unpause music
        if self.music_initialized:
            if self.game_paused:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()
    
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        try:
            current_flags = self.screen.get_flags()
            if current_flags & pygame.FULLSCREEN:
                # Switch to windowed mode
                self.screen = pygame.display.set_mode((1200, 800), pygame.RESIZABLE)
                print("Switched to windowed mode")
            else:
                # Switch to fullscreen mode
                self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
                print("Switched to fullscreen mode")
            
            # Update world_to_screen_scale for new window size
            current_width, current_height = self.screen.get_size()
            self.world_to_screen_scale = min(current_width, current_height) // 15
            
        except Exception as e:
            print(f"Failed to toggle fullscreen: {e}")
    
    def handle_input(self, keys_pressed, events):
        """Handle input events"""
        for event in events:
            if event.type == pygame.KEYDOWN:
                # ESC key to toggle fullscreen/windowed mode
                if event.key == pygame.K_ESCAPE:
                    self.toggle_fullscreen()
                
                # Alt+F4 or Ctrl+Q to quit
                elif (event.key == pygame.K_F4 and (keys_pressed[pygame.K_LALT] or keys_pressed[pygame.K_RALT])) or \
                     (event.key == pygame.K_q and (keys_pressed[pygame.K_LCTRL] or keys_pressed[pygame.K_RCTRL])):
                    pygame.quit()
                    sys.exit()
                
                # P key to pause/unpause
                elif event.key == pygame.K_p and self.game_running:
                    self.toggle_pause()
                
                elif event.key == pygame.K_SPACE and self.game_running and not self.game_paused:
                    if not self.is_jumping:
                        self.velocity = self.jump_force
                        self.is_jumping = True
                    elif self.player_y < self.max_jump_height and self.velocity > 0:
                        self.velocity += self.jump_force * self.air_control * 0.3
                
                elif event.key == pygame.K_r and not self.game_running:
                    self.restart_game()
                
                # Debug: Score to 999
                elif event.key == pygame.K_F1 and self.game_running and not self.game_paused:
                    self.score = 999
                    self.update_difficulty()
                    self.show_999_forever = True
    
    def restart_game(self):
        """Restart the game - keep music playing"""
        self.reset_game_state()
        self.last_spawn_time = time.time()
        self.last_lifeline_spawn_time = time.time()
        self.game_over_screen = False
        
        # Don't restart music - let it continue playing
        # Only ensure it's playing if it somehow stopped
        if self.music_initialized and not pygame.mixer.music.get_busy():
            try:
                music_path = resource_path('assets/sounds/Afterlife.mp3')
                if os.path.exists(music_path):
                    pygame.mixer.music.load(music_path)
                    pygame.mixer.music.play(-1)
            except:
                pass
    
    def draw(self):
        """Draw everything to the screen"""
        # Clear screen
        self.screen.fill(BLACK)
        
        # Get current screen size for proper scaling
        current_width, current_height = self.screen.get_size()
        
        # Draw background
        if self.bg_texture:
            # Scale background to current screen size
            scaled_bg = pygame.transform.scale(self.bg_texture, (current_width, current_height))
            self.screen.blit(scaled_bg, (0, 0))
        else:
            self.screen.fill(LIGHT_GRAY)
        
        # Draw ground tiles (single layer with extended height to fill bottom)
        for tile in self.ground_tiles:
            screen_x, screen_y = self.world_to_screen(tile['x'], tile['y'])
            tile_width = int(4 * self.world_to_screen_scale)
            tile_height = int(4.0 * self.world_to_screen_scale)  # Increased height significantly
            
            if self.tiles_texture:
                scaled_texture = pygame.transform.scale(self.tiles_texture, (tile_width, tile_height))
                self.screen.blit(scaled_texture, (screen_x - tile_width//2, screen_y - tile_height//2))
            else:
                pygame.draw.rect(self.screen, GRAY, 
                               (screen_x - tile_width//2, screen_y - tile_height//2, tile_width, tile_height))
        
        # Draw obstacles (only render those visible on screen - updated range)
        for i, obs in enumerate(self.obstacles):
            # Only draw obstacles that are on screen (expanded visible range to account for new spawn distance)
            if obs['x'] > -15 and obs['x'] < 20:  # Expanded visible range (was -8 to 12)
                screen_x, screen_y = self.world_to_screen(obs['x'], obs['y'])
                size = int(obs['width'] * self.world_to_screen_scale)
                
                if self.pills_texture:
                    scaled_texture = pygame.transform.scale(self.pills_texture, (size, size))
                    self.screen.blit(scaled_texture, (screen_x - size//2, screen_y - size//2))
                else:
                    pygame.draw.rect(self.screen, RED, 
                                   (screen_x - size//2, screen_y - size//2, size, size))
        
        # Draw lifelines (only render those visible on screen - updated range)
        for i, lifeline in enumerate(self.lifelines):
            # Only draw lifelines that are on screen (expanded visible range to account for new spawn distance)
            if lifeline['x'] > -15 and lifeline['x'] < 20:  # Expanded visible range (was -8 to 12)
                screen_x, screen_y = self.world_to_screen(lifeline['x'], lifeline['y'])
                size = int(lifeline['width'] * self.world_to_screen_scale)
                
                if self.lifeline_texture:
                    scaled_texture = pygame.transform.scale(self.lifeline_texture, (size, size))
                    self.screen.blit(scaled_texture, (screen_x - size//2, screen_y - size//2))
                else:
                    pygame.draw.rect(self.screen, GREEN, 
                                   (screen_x - size//2, screen_y - size//2, size, size))
        
        # Draw player with proper scaling
        screen_x, screen_y = self.world_to_screen(self.player_x, self.player_y)
        player_size = int(2.5 * self.world_to_screen_scale)  # Increased player size
        
        # Handle player flashing during invulnerability
        draw_player = True
        if self.invulnerable:
            flash_speed = 10
            if int(time.time() * flash_speed) % 2:
                draw_player = True
            else:
                draw_player = False
        
        if draw_player:
            if self.juice_texture:
                # Scale texture to proper size
                scaled_texture = pygame.transform.scale(self.juice_texture, (player_size, player_size))
                if self.player_rotation != 0:
                    rotated_texture = pygame.transform.rotate(scaled_texture, self.player_rotation)
                    rotated_rect = rotated_texture.get_rect(center=(screen_x, screen_y))
                    self.screen.blit(rotated_texture, rotated_rect)
                else:
                    self.screen.blit(scaled_texture, (screen_x - player_size//2, screen_y - player_size//2))
            else:
                color = AZURE if self.is_jumping else CYAN
                if self.invulnerable:
                    color = LIME if self.is_jumping else CYAN
                pygame.draw.rect(self.screen, color,
                               (screen_x - player_size//2, screen_y - player_size//2, player_size, player_size))
        
        # Draw UI
        self.draw_ui()
        
        # Draw pause screen
        if self.game_paused:
            self.draw_pause_screen()
        
        # Draw game over screen
        if self.game_over_screen:
            self.draw_game_over()
    
    def draw_ui(self):
        """Draw the user interface - adapted for fullscreen"""
        # Calculate UI positions based on screen size
        current_width, current_height = self.screen.get_size()
        ui_margin = int(current_width * 0.02)  # 2% of screen width for margin
        ui_font_size = max(24, int(current_height * 0.03))  # Adaptive font size
        
        # Create fonts based on screen size
        ui_font = pygame.font.Font(None, ui_font_size)
        
        # Score
        if self.show_999_forever:
            score_text = ui_font.render("999 FOREVER", True, GOLD)
        else:
            score_text = ui_font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (ui_margin, ui_margin))
        
        # Lives
        lives_text = ui_font.render(f"Lives: {self.lives}", True, WHITE)
        self.screen.blit(lives_text, (ui_margin, ui_margin + ui_font_size + 10))
        
        # Difficulty
        difficulty_text = ui_font.render(f"Level: {self.difficulty_level}", True, WHITE)
        self.screen.blit(difficulty_text, (ui_margin, ui_margin + (ui_font_size + 10) * 2))
        
        # Speed indicator (Chrome Dino style)
        speed_percent = int((self.get_current_speed() / self.base_speed - 1) * 100)
        if speed_percent > 0:
            speed_text = ui_font.render(f"Speed: +{speed_percent}%", True, YELLOW)
            self.screen.blit(speed_text, (ui_margin, ui_margin + (ui_font_size + 10) * 3))
        
        # ESC to toggle fullscreen and quit instructions
        exit_font = pygame.font.Font(None, max(16, int(current_height * 0.02)))
        
        esc_text = exit_font.render("ESC = Fullscreen", True, LIGHT_GRAY)
        self.screen.blit(esc_text, (current_width - 150, ui_margin))
        
        quit_text = exit_font.render("Alt+F4 = Quit", True, LIGHT_GRAY)
        self.screen.blit(quit_text, (current_width - 150, ui_margin + 20))
        
        # Pause instruction (only show when game is running)
        if self.game_running and not self.game_over_screen:
            pause_text = exit_font.render("P = Pause", True, LIGHT_GRAY)
            self.screen.blit(pause_text, (current_width - 150, ui_margin + 40))
    
    def draw_pause_screen(self):
        """Draw the pause screen"""
        # Semi-transparent overlay
        current_width, current_height = self.screen.get_size()
        overlay = pygame.Surface((current_width, current_height))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Pause panel
        panel_width = int(current_width * 0.6)
        panel_height = int(current_height * 0.4)
        panel_x = (current_width - panel_width) // 2
        panel_y = (current_height - panel_height) // 2
        
        pygame.draw.rect(self.screen, DARK_GRAY, (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_width, panel_height), 3)
        
        # Pause text
        pause_text = self.font_huge.render("PAUSED", True, YELLOW)
        text_rect = pause_text.get_rect(center=(current_width//2, panel_y + 80))
        self.screen.blit(pause_text, text_rect)
        
        # Instructions
        resume_text = self.font_medium.render("Press 'P' to resume", True, WHITE)
        text_rect = resume_text.get_rect(center=(current_width//2, panel_y + 140))
        self.screen.blit(resume_text, text_rect)
        
        # Current stats during pause
        stats_y = panel_y + 180
        stats_font = pygame.font.Font(None, max(20, int(current_height * 0.025)))
        
        score_text = stats_font.render(f"Score: {self.score}", True, LIGHT_GRAY)
        text_rect = score_text.get_rect(center=(current_width//2 - 100, stats_y))
        self.screen.blit(score_text, text_rect)
        
        lives_text = stats_font.render(f"Lives: {self.lives}", True, LIGHT_GRAY)
        text_rect = lives_text.get_rect(center=(current_width//2, stats_y))
        self.screen.blit(lives_text, text_rect)
        
        level_text = stats_font.render(f"Level: {self.difficulty_level}", True, LIGHT_GRAY)
        text_rect = level_text.get_rect(center=(current_width//2 + 100, stats_y))
        self.screen.blit(level_text, text_rect)
    
    def draw_game_over(self):
        """Draw the game over screen"""
        # Semi-transparent overlay
        current_width, current_height = self.screen.get_size()
        overlay = pygame.Surface((current_width, current_height))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Game over panel
        panel_width = int(current_width * 0.8)
        panel_height = int(current_height * 0.6)
        panel_x = (current_width - panel_width) // 2
        panel_y = (current_height - panel_height) // 2
        
        pygame.draw.rect(self.screen, DARK_GRAY, (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(self.screen, WHITE, (panel_x, panel_y, panel_width, panel_height), 3)
        
        # Game over text
        if self.score >= 999:
            game_over_text = self.font_huge.render("999 FOREVER", True, GOLD)
        else:
            game_over_text = self.font_huge.render("GAME OVER", True, RED)
        
        text_rect = game_over_text.get_rect(center=(current_width//2, panel_y + 100))
        self.screen.blit(game_over_text, text_rect)
        
        # Final score
        score_text = self.font_medium.render(f"Final Score: {self.score}", True, WHITE)
        text_rect = score_text.get_rect(center=(current_width//2, panel_y + 180))
        self.screen.blit(score_text, text_rect)
        
        # Level reached
        level_text = self.font_medium.render(f"Reached Level: {self.difficulty_level}", True, YELLOW)
        text_rect = level_text.get_rect(center=(current_width//2, panel_y + 220))
        self.screen.blit(level_text, text_rect)
        
        # Restart instruction
        restart_text = self.font_medium.render("Press 'R' to restart", True, LIGHT_GRAY)
        text_rect = restart_text.get_rect(center=(current_width//2, panel_y + 300))
        self.screen.blit(restart_text, text_rect)
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            dt = self.clock.tick(FPS) / 1000.0  # Delta time in seconds
            
            # Handle events
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
            
            # Handle input
            keys_pressed = pygame.key.get_pressed()
            self.handle_input(keys_pressed, events)
            
            # Update game
            self.update(dt)
            
            # Draw everything
            self.draw()
            
            # Update display
            pygame.display.flip()
        
        # Cleanup
        pygame.mixer.quit()
        pygame.quit()
        sys.exit()

# Run the game
if __name__ == "__main__":
    game = Game()
    game.run()