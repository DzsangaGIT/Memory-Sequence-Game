import pygame
import sys
import random
import os

# Initialize pygame
pygame.init()
pygame.mixer.init()

# ------------------- Constants -------------------
# Screen dimensions
WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Memory Sequence Game")

# Colors (Modern Dark Mode Palette)
DARK_BACKGROUND = (25, 25, 25)
BUTTON_GREY = (70, 70, 70)
BUTTON_HIGHLIGHT = (50, 205, 50)  # Lime Green
BUTTON_HOVER = (90, 90, 90)       # Slightly lighter grey for hover
BUTTON_BORDER = (200, 200, 200)
TEXT_COLOR = (220, 220, 220)
SHADOW_COLOR = (0, 0, 0, 100)    # Semi-transparent black for shadows

# Fonts
try:
    TITLE_FONT = pygame.font.Font(os.path.join("assets", "fonts", "Helvetica.ttf"), 64)
    BUTTON_FONT = pygame.font.Font(os.path.join("assets", "fonts", "Helvetica.ttf"), 32)
    SCORE_FONT = pygame.font.Font(os.path.join("assets", "fonts", "Helvetica.ttf"), 48)
except:
    # Fallback to default pygame font if custom fonts not found
    TITLE_FONT = pygame.font.SysFont('Helvetica', 64, bold=True)
    BUTTON_FONT = pygame.font.SysFont('Helvetica', 32)
    SCORE_FONT = pygame.font.SysFont('Helvetica', 48)

# Frames per second
FPS = 60
CLOCK = pygame.time.Clock()

# Button parameters
BUTTON_SIZE = 150
BUTTON_PADDING = 30
MAX_BUTTONS = 10  # Maximum buttons allowed

# Animation parameters
HIGHLIGHT_ANIMATION_STEPS = 20
HIGHLIGHT_ANIMATION_SPEED = 0.03  # Speed of color transition
HOVER_ANIMATION_SPEED = 0.05      # Speed of hover scaling

# Sound paths (ensure you have these sound files in the 'assets/sounds' directory)
BUTTON_CLICK_SOUND_PATH = os.path.join("assets", "sounds", "button_click.wav")
GAME_OVER_SOUND_PATH = os.path.join("assets", "sounds", "game_over.wav")

# Load sounds
try:
    BUTTON_CLICK_SOUND = pygame.mixer.Sound(BUTTON_CLICK_SOUND_PATH)
    GAME_OVER_SOUND = pygame.mixer.Sound(GAME_OVER_SOUND_PATH)
except:
    BUTTON_CLICK_SOUND = None
    GAME_OVER_SOUND = None

# ------------------- Classes -------------------
class Button:
    def __init__(self, rect, id):
        self.rect = rect
        self.id = id
        self.base_color = BUTTON_GREY
        self.highlight_color = BUTTON_HIGHLIGHT
        self.hover_color = BUTTON_HOVER
        self.current_color = self.base_color
        self.target_color = self.base_color
        self.animation_step = 0
        self.animating = False
        self.hovered = False
        self.scale = 1.0
        self.target_scale = 1.0
        self.scale_step = 0
        self.scaling = False

    def draw(self, screen):
        # Draw shadow
        shadow_rect = self.rect.copy()
        shadow_rect.x += 5
        shadow_rect.y += 5
        shadow_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, SHADOW_COLOR, shadow_surface.get_rect(), border_radius=15)
        screen.blit(shadow_surface, shadow_rect.topleft)

        # Apply scaling for hover effect
        scaled_width = int(self.rect.width * self.scale)
        scaled_height = int(self.rect.height * self.scale)
        scaled_rect = pygame.Rect(
            self.rect.centerx - scaled_width // 2,
            self.rect.centery - scaled_height // 2,
            scaled_width,
            scaled_height
        )

        # Draw button
        pygame.draw.rect(screen, self.current_color, scaled_rect, border_radius=15)
        pygame.draw.rect(screen, BUTTON_BORDER, scaled_rect, 3, border_radius=15)

    def is_clicked(self, pos):
        # Adjust for scaling
        scaled_width = int(self.rect.width * self.scale)
        scaled_height = int(self.rect.height * self.scale)
        scaled_rect = pygame.Rect(
            self.rect.centerx - scaled_width // 2,
            self.rect.centery - scaled_height // 2,
            scaled_width,
            scaled_height
        )
        return scaled_rect.collidepoint(pos)

    def start_highlight(self):
        self.target_color = self.highlight_color
        self.animating = True
        self.animation_step = 0

    def start_unhighlight(self):
        self.target_color = self.base_color
        self.animating = True
        self.animation_step = 0

    def start_hover(self):
        self.target_color = self.hover_color
        self.target_scale = 1.05  # Slightly larger
        self.scaling = True
        self.animation_step = 0

    def end_hover(self):
        self.target_color = self.base_color
        self.target_scale = 1.0
        self.scaling = True
        self.animation_step = 0

    def update(self):
        # Handle color transitions
        if self.animating:
            r, g, b = self.current_color
            tr, tg, tb = self.target_color

            # Calculate the difference
            dr = (tr - r) * HIGHLIGHT_ANIMATION_SPEED
            dg = (tg - g) * HIGHLIGHT_ANIMATION_SPEED
            db = (tb - b) * HIGHLIGHT_ANIMATION_SPEED

            # Update current color
            self.current_color = (
                r + dr,
                g + dg,
                b + db
            )

            self.animation_step += 1

            # Check if the color is close enough to target
            if (abs(r - tr) < 1 and abs(g - tg) < 1 and abs(b - tb) < 1) or self.animation_step >= HIGHLIGHT_ANIMATION_STEPS:
                self.current_color = self.target_color
                self.animating = False

        # Handle hover scaling
        if self.scaling:
            if self.scale < self.target_scale:
                self.scale += HOVER_ANIMATION_SPEED
                if self.scale >= self.target_scale:
                    self.scale = self.target_scale
                    self.scaling = False
            elif self.scale > self.target_scale:
                self.scale -= HOVER_ANIMATION_SPEED
                if self.scale <= self.target_scale:
                    self.scale = self.target_scale
                    self.scaling = False

class Game:
    def __init__(self):
        self.state = "TITLE"  # Possible states: TITLE, DIFFICULTY, GAME, GAME_OVER
        self.buttons = create_buttons(4)
        self.sequence = []
        self.user_sequence = []
        self.score = 0
        self.num_buttons = 4
        self.max_buttons = MAX_BUTTONS
        self.fonts = {
            "title": TITLE_FONT,
            "button": BUTTON_FONT,
            "score": SCORE_FONT,
            "difficulty": BUTTON_FONT
        }
        self.difficulty = "Normal"  # Default difficulty
        self.display_speed = 500  # milliseconds between highlights in Normal mode
        self.fast_display_speed = 100  # minimal delay in Fast mode

    def reset_game(self):
        self.sequence = []
        self.user_sequence = []
        self.score = 0
        self.num_buttons = 4
        self.buttons = create_buttons(self.num_buttons)

    def add_buttons(self, count=2):
        """
        Add 'count' number of buttons to the game, up to the maximum allowed.
        """
        for _ in range(count):
            if self.num_buttons < self.max_buttons:
                self.num_buttons += 1
        self.buttons = create_buttons(self.num_buttons)

    def add_to_sequence(self):
        self.sequence.append(random.randint(0, self.num_buttons -1))

    def draw_title_screen(self):
        SCREEN.fill(DARK_BACKGROUND)
        # Title
        title_text = self.fonts["title"].render("Memory Sequence", True, TEXT_COLOR)
        title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 100))
        SCREEN.blit(title_text, title_rect)

        # Start Button
        start_button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 50, 200, 60)
        start_button = Button(start_button_rect, -1)  # ID -1 for Start Button
        start_button.current_color = BUTTON_GREY
        start_button.draw(SCREEN)

        # Start Text
        start_text = self.fonts["button"].render("Start", True, TEXT_COLOR)
        start_text_rect = start_text.get_rect(center=start_button_rect.center)
        SCREEN.blit(start_text, start_text_rect)

        pygame.display.flip()

    def draw_difficulty_screen(self):
        SCREEN.fill(DARK_BACKGROUND)
        # Difficulty Title
        difficulty_title = self.fonts["title"].render("Select Difficulty", True, TEXT_COLOR)
        difficulty_title_rect = difficulty_title.get_rect(center=(WIDTH//2, HEIGHT//2 - 150))
        SCREEN.blit(difficulty_title, difficulty_title_rect)

        # Normal Button
        normal_button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 50, 200, 60)
        normal_button = Button(normal_button_rect, 0)  # ID 0 for Normal
        normal_button.draw(SCREEN)
        normal_text = self.fonts["button"].render("Normal", True, TEXT_COLOR)
        normal_text_rect = normal_text.get_rect(center=normal_button_rect.center)
        SCREEN.blit(normal_text, normal_text_rect)

        # Fast Button
        fast_button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 50, 200, 60)
        fast_button = Button(fast_button_rect, 1)  # ID 1 for Fast
        fast_button.draw(SCREEN)
        fast_text = self.fonts["button"].render("Fast", True, TEXT_COLOR)
        fast_text_rect = fast_text.get_rect(center=fast_button_rect.center)
        SCREEN.blit(fast_text, fast_text_rect)

        pygame.display.flip()

    def draw_game_over_screen(self):
        SCREEN.fill(DARK_BACKGROUND)
        # Game Over Text
        game_over_text = self.fonts["title"].render("Game Over", True, TEXT_COLOR)
        game_over_rect = game_over_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 100))
        SCREEN.blit(game_over_text, game_over_rect)

        # Score Text
        score_text = self.fonts["score"].render(f"Score: {self.score}", True, TEXT_COLOR)
        score_rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2))
        SCREEN.blit(score_text, score_rect)

        # Restart Button
        restart_button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 100, 200, 60)
        restart_button = Button(restart_button_rect, -2)  # ID -2 for Restart Button
        restart_button.draw(SCREEN)

        # Restart Text
        restart_text = self.fonts["button"].render("Restart", True, TEXT_COLOR)
        restart_text_rect = restart_text.get_rect(center=restart_button_rect.center)
        SCREEN.blit(restart_text, restart_text_rect)

        pygame.display.flip()

    def draw_buttons(self):
        for button in self.buttons:
            button.draw(SCREEN)

    def animate_sequence(self):
        for button_id in self.sequence:
            button = self.buttons[button_id]
            button.start_highlight()
            if BUTTON_CLICK_SOUND:
                BUTTON_CLICK_SOUND.play()
            for _ in range(HIGHLIGHT_ANIMATION_STEPS):
                SCREEN.fill(DARK_BACKGROUND)
                self.draw_buttons()
                for btn in self.buttons:
                    btn.update()
                    btn.draw(SCREEN)
                pygame.display.flip()
                CLOCK.tick(FPS)
            pygame.time.delay(self.fast_display_speed if self.difficulty == "Fast" else self.display_speed)
            button.start_unhighlight()
            for _ in range(HIGHLIGHT_ANIMATION_STEPS):
                SCREEN.fill(DARK_BACKGROUND)
                self.draw_buttons()
                for btn in self.buttons:
                    btn.update()
                    btn.draw(SCREEN)
                pygame.display.flip()
                CLOCK.tick(FPS)
            pygame.time.delay(100)

    def run_gameplay(self):
        self.reset_game()
        running = True
        while running:
            SCREEN.fill(DARK_BACKGROUND)
            self.draw_buttons()
            pygame.display.flip()

            pygame.time.delay(500)

            # Add to sequence and animate
            self.add_to_sequence()
            self.animate_sequence()

            # User input phase
            self.user_sequence = []
            for idx in range(len(self.sequence)):
                user_input = None
                while user_input is None:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            pos = pygame.mouse.get_pos()
                            for button in self.buttons:
                                if button.is_clicked(pos):
                                    user_input = button.id
                                    button.start_highlight()
                                    if BUTTON_CLICK_SOUND:
                                        BUTTON_CLICK_SOUND.play()
                                    # Animate button press
                                    for _ in range(HIGHLIGHT_ANIMATION_STEPS):
                                        SCREEN.fill(DARK_BACKGROUND)
                                        self.draw_buttons()
                                        for btn in self.buttons:
                                            btn.update()
                                            btn.draw(SCREEN)
                                        pygame.display.flip()
                                        CLOCK.tick(FPS)
                                    pygame.time.delay(100)
                                    button.start_unhighlight()
                                    for _ in range(HIGHLIGHT_ANIMATION_STEPS):
                                        SCREEN.fill(DARK_BACKGROUND)
                                        self.draw_buttons()
                                        for btn in self.buttons:
                                            btn.update()
                                            btn.draw(SCREEN)
                                        pygame.display.flip()
                                        CLOCK.tick(FPS)
                                    self.user_sequence.append(user_input)
                                    # Check correctness
                                    if user_input != self.sequence[idx]:
                                        if GAME_OVER_SOUND:
                                            GAME_OVER_SOUND.play()
                                        running = False
                                    break
                    CLOCK.tick(FPS)
                if not running:
                    break

            if not running:
                break

            # User completed the sequence correctly
            self.score +=1

            # Dynamically add more buttons in pairs
            if self.score % 5 ==0 and self.num_buttons < self.max_buttons:
                self.add_buttons(count=2)
                pygame.time.delay(300)

        # After game loop ends, transition to Game Over
        self.state = "GAME_OVER"

    def run(self):
        while True:
            if self.state == "TITLE":
                self.draw_title_screen()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        pos = pygame.mouse.get_pos()
                        # Check if Start button is clicked
                        start_button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 50, 200, 60)
                        if start_button_rect.collidepoint(pos):
                            self.state = "DIFFICULTY"
                            break
                pygame.display.flip()
                CLOCK.tick(FPS)

            elif self.state == "DIFFICULTY":
                self.draw_difficulty_screen()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        pos = pygame.mouse.get_pos()
                        # Check if Normal button is clicked
                        normal_button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 50, 200, 60)
                        if normal_button_rect.collidepoint(pos):
                            self.difficulty = "Normal"
                            self.display_speed = 500  # milliseconds
                            self.fast_display_speed = 100  # minimal delay
                            self.state = "GAME"
                            break
                        # Check if Fast button is clicked
                        fast_button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 50, 200, 60)
                        if fast_button_rect.collidepoint(pos):
                            self.difficulty = "Fast"
                            self.display_speed = 100  # faster display
                            self.fast_display_speed = 50  # minimal delay
                            self.state = "GAME"
                            break
                pygame.display.flip()
                CLOCK.tick(FPS)

            elif self.state == "GAME":
                self.run_gameplay()
                self.state = "GAME_OVER"

            elif self.state == "GAME_OVER":
                self.draw_game_over_screen()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        pos = pygame.mouse.get_pos()
                        # Check if Restart button is clicked
                        restart_button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 100, 200, 60)
                        if restart_button_rect.collidepoint(pos):
                            self.state = "TITLE"
                            break
                pygame.display.flip()
                CLOCK.tick(FPS)

# ------------------- Helper Functions -------------------
def create_buttons(num_buttons):
    buttons = []
    # Determine grid size (square as much as possible)
    grid_cols = grid_rows = int(num_buttons ** 0.5)
    if grid_cols ** 2 < num_buttons:
        grid_cols += 1
    if grid_cols * grid_rows < num_buttons:
        grid_rows +=1

    # Calculate total grid size
    total_width = grid_cols * BUTTON_SIZE + (grid_cols - 1) * BUTTON_PADDING
    total_height = grid_rows * BUTTON_SIZE + (grid_rows -1) * BUTTON_PADDING

    # Starting positions to center the grid
    start_x = (WIDTH - total_width) // 2
    start_y = (HEIGHT - total_height) // 2

    for i in range(num_buttons):
        row = i // grid_cols
        col = i % grid_cols
        x = start_x + col * (BUTTON_SIZE + BUTTON_PADDING)
        y = start_y + row * (BUTTON_SIZE + BUTTON_PADDING)
        rect = pygame.Rect(x, y, BUTTON_SIZE, BUTTON_SIZE)
        buttons.append(Button(rect, i))
    return buttons

# ------------------- Main Execution -------------------
if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit()
