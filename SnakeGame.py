from machine import Pin, I2C
import ssd1306
import utime
from random import randint

# Inicializa o display OLED (128x64) via I2C
i2c = I2C(0, scl=Pin(17), sda=Pin(16))
display = ssd1306.SSD1306_I2C(128, 64, i2c)

# Define tamanho do display e dos blocos
width = 128
height = 64
tile_size = 8
grid_w, grid_h = width // tile_size, height // tile_size

# === Teclado 4x4 ===
keymap = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D']
]

# Define os pinos do teclado
rows = [Pin(pin, Pin.OUT) for pin in (2, 3, 4, 5)]
cols = [Pin(pin, Pin.IN, Pin.PULL_DOWN) for pin in (6, 7, 8, 9)]

# Lê uma tecla pressionada no teclado
def read_keypad():
    for i, row in enumerate(rows):
        row.high()
        for j, col in enumerate(cols):
            if col.value():
                row.low()
                return keymap[i][j]
        row.low()
    return None

# === Classe do Nó da cobra ===
class SnakeNode:
    def __init__(self, position=None, direction=None, next=None):
        self.pos = position  
        self.dir = direction 
        self.next = next     

# === Classe da Cobra ===
class Snake:
    def __init__(self):
        center = (grid_w // 2, grid_h // 2)  
        self.direction = (0, 0)  
        self.head = SnakeNode(center, self.direction)

    def push(self, new_head):  
        new_head.next, self.head = self.head, new_head

    def pop(self): 
        current = self.head
        prev = None
        while current.next:
            prev = current
            current = current.next
        if prev:
            prev.next = None

    def contains(self, pos):  
        node = self.head
        while node:
            if node.pos == pos:
                return True
            node = node.next
        return False

    def move(self):  
        dx, dy = self.direction
        x, y = self.head.pos
        x += dx
        y += dy
        return SnakeNode((x, y), self.direction)

    def update_direction(self, pressed):
        dx, dy = self.direction
        if pressed.get('A') and dx == 0:  
            dx, dy = -1, 0
        elif pressed.get('Y') and dx == 0:  
            dx, dy = 1, 0
        elif pressed.get('B') and dy == 0:  
            dx, dy = 0, 1
        elif pressed.get('X') and dy == 0:  
            dx, dy = 0, -1
        if (dx, dy) != (0, 0):
            self.direction = dx, dy

    def show(self):  
        node = self.head
        while node:
            x, y = node.pos
            display.fill_rect(x * tile_size, y * tile_size, tile_size, tile_size, 1)
            node = node.next

    def moving(self):
        return self.direction != (0, 0)

# === Classe da Comida ===
class Food:
    def __init__(self, snake):
        self.reset_position(snake)

    def reset_position(self, snake):  
        while True:
            pos = (randint(0, grid_w - 1), randint(0, grid_h - 1))
            if not snake.contains(pos):
                self.pos = pos
                break

    def show(self):  
        x, y = self.pos
        display.fill_rect(x * tile_size + 2, y * tile_size + 2, tile_size - 4, tile_size - 4, 1)

# === Classe do Jogo ===
class Game:
    def __init__(self):
        self.reset()

    def reset(self):  
        self.snake = Snake()
        self.food = Food(self.snake)
        self.score = 0
        self.base_refresh = 0.1
        self.pressed = {'A': False, 'B': False, 'X': False, 'Y': False}
        self.paused = True
        self.game_over = False

    def update_inputs(self):  
        key = read_keypad()
        self.pressed = {'A': False, 'B': False, 'X': False, 'Y': False}

        if key == '#': self.pressed['A'] = True  
        elif key == '6': self.pressed['Y'] = True
        elif key == '8': self.pressed['B'] = True
        elif key == 'C': self.pressed['X'] = True
        elif key == '*':  
            if self.game_over:
                self.reset()
            else:
                self.paused = not self.paused
            utime.sleep(0.3)

    def tick(self):  
        self.update_inputs()

        if self.game_over:
            display.fill(0)
            display.text("GAME OVER", 20, 20, 1)
            display.text("Score: " + str(self.score), 20, 40, 1)
            display.show()
            utime.sleep(self.base_refresh)
            return

        if self.paused or not self.snake.moving():
            self.snake.update_direction(self.pressed)
            display.fill(0)
            display.text("PAUSED", 40, 20, 1)
            display.text("Score: " + str(self.score), 20, 40, 1)
            display.show()
            utime.sleep(self.base_refresh)
            return

        self.snake.update_direction(self.pressed)
        new_head = self.snake.move()

        # === MODIFICAÇÃO AQUI: wrap-around nas bordas ===
        x, y = new_head.pos
        x %= grid_w
        y %= grid_h
        new_head.pos = (x, y)

        if self.snake.contains(new_head.pos):
            self.game_over = True
            return

        if new_head.pos == self.food.pos:
            self.snake.push(new_head)
            self.food.reset_position(self.snake)
            self.score += 1
        else:
            self.snake.push(new_head)
            self.snake.pop()

        display.fill(0)
        self.food.show()
        self.snake.show()
        display.text("Score: " + str(self.score), 0, 0, 1)
        display.show()
        utime.sleep(self.base_refresh)

# === Loop principal ===
game = Game()
while True:
    game.tick()

