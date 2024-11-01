import heapq
import time
import tracemalloc
import threading
import pygame
import os
from collections import deque
import copy
import psutil
from queue import Queue

# Pygame Configuration
TILE_SIZE = 50
WINDOW_WIDTH = 200
WINDOW_HEIGHT = 200
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SELECTED_COLOR = (173, 216, 230)

# Mảng lưu các vị trí deadlock bất biến
deadfield = []

# Đặt vị trí cửa sổ lên góc trên cùng bên trái
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,30"

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
screen.fill(WHITE)
# pygame.display.set_caption("AAres Pushes Stones - Choose File & Algorithm")
font = pygame.font.SysFont('Arial', 20)
BUTTON_PANEL_SIZE = 75  # Độ rộng khu vực chứa các nút

# Tải hình ảnh
ares_img = pygame.transform.scale(pygame.image.load("image/ares.png"), (TILE_SIZE, TILE_SIZE))
stone_img = pygame.transform.scale(pygame.image.load("image/stone.png"), (TILE_SIZE, TILE_SIZE))
switch_img = pygame.transform.scale(pygame.image.load("image/switch.png"), (TILE_SIZE, TILE_SIZE))
wall_img = pygame.transform.scale(pygame.image.load("image/wall.png"), (TILE_SIZE, TILE_SIZE))
empty_img = pygame.transform.scale(pygame.image.load("image/tile.png"), (TILE_SIZE, TILE_SIZE))
reset_button = pygame.transform.scale(pygame.image.load("image/reset_button.png"), (TILE_SIZE, TILE_SIZE))
start_button = pygame.transform.scale(pygame.image.load("image/start_button.png"), (TILE_SIZE, TILE_SIZE))
pause_button = pygame.transform.scale(pygame.image.load("image/pause_button.png"), (TILE_SIZE, TILE_SIZE))
menu_button = pygame.transform.scale(pygame.image.load("image/menu_button.png"), (TILE_SIZE, TILE_SIZE))

# Tải âm thanh
click_effect = pygame.mixer.Sound("sound/click.wav")
walk_effect = pygame.mixer.Sound('sound/6.ogg')

# Danh sách thuật toán
ALGORITHMS = ["BFS", "IDDFS", "UCS", "A*"]

# Biến toàn cục: lưu hướng đi với ký tự thường
DIRECTIONS = [
    ((-1, 0), 'u'),  # Up
    ((0, 1), 'r'),    # Right
    ((1, 0), 'd'),   # Down
    ((0, -1), 'l')  # Left
]

# Chọn thuật toán sử dụng
def search_algorithm(algorithm, maze, ares, stones, switches, weights, deadfield):
    if algorithm == "BFS":
        return bfs(maze, ares, stones, switches, weights, deadfield)
    elif algorithm == "IDDFS":
         return iddfs(maze, ares, stones, switches, weights, deadfield)
    elif algorithm == "UCS":
        return ucs(maze, ares, stones, switches, weights, deadfield)
    elif algorithm == "A*":
        return astar(maze, ares, stones, switches, weights, deadfield)
    else:
        raise ValueError(f"Thuật toán {algorithm} không hợp lệ.")

# Đọc mê cung từ tệp
def load_maze(file_name):
    with open(file_name, 'r') as f:
        weights = list(map(int, f.readline().split()))  # Đọc trọng lượng đá
        maze = [list(line.rstrip()) for line in f.readlines()]

    return weights, maze

def inside_maze(maze, ares):
    inside = copy.deepcopy(maze)
    
    q = Queue()
    q.put(ares)
    while not q.empty():
        pos = q.get()
        inside[pos[0]][pos[1]] = 'V'
        for (dr,dc), _ in DIRECTIONS:
            new_r = dr + pos[0]
            new_c = dc + pos[1]
            
            if maze[new_r][new_c] != '#' and inside[new_r][new_c] != 'V':
                q.put((new_r, new_c))
                
    return inside

# Hàm tính kích thước cửa sổ phù hợp với kích thước map
def calculate_window_size(maze):
    rows = len(maze)
    cols = max(len(row) for row in maze)

    # Tính kích thước của bản đồ
    width = cols * TILE_SIZE
    height = rows * TILE_SIZE

    return width, height

# Hàm tìm vị trí ares, đấ và công tắc
def find_positions(maze):
    ares, stones, switches = None, [], []
    for i, row in enumerate(maze):
        for j, cell in enumerate(row):
            if cell in {'@', '+'}:
                ares = (i, j)
            if cell in {'$', '*'}:
                stones.append((i, j))
            if cell in {'.', '+', '*'}:
                switches.append((i, j))
    return ares, stones, switches

def is_goal_state(stones, switches):
    """Kiểm tra xem tất cả các viên đá đã ở vị trí công tắc hay chưa."""
    return all(stone in switches for stone in stones)

def is_valid(x, y, maze):
    """Kiểm tra tính hợp lệ của vị trí (x, y) trong mê cung."""
    return 0 <= x < len(maze) and 0 <= y < len(maze[x]) and maze[x][y] != '#'

# Thuât toán BFS
def bfs(maze, ares, stones, switches, weights, deadfield):
    """Tìm đường đi từ vị trí Ares tới mục tiêu bằng BFS."""
    start_memory = psutil.Process(os.getpid()).memory_info().rss
    start_time = time.time()
    
    queue = deque([(ares, tuple(stones), "", 0)])
    visited = set()
    node_count = 0
    
    visited.add((ares, tuple(stones)))

    while queue:
        cur_pos, cur_stones, path, total_weight = queue.popleft()
        if is_goal_state(cur_stones, switches):
            end_time = time.time()
            end_memory = psutil.Process(os.getpid()).memory_info().rss
            memory_used = (end_memory - start_memory) / (1024 * 1024)
            return {
                'steps': len(path),
                'weight': total_weight,
                'nodes': node_count,
                'time': (end_time - start_time) * 1000,
                'memory': memory_used,
                'path': path
            }

        for (dx, dy), char in DIRECTIONS:
            new_x, new_y = cur_pos[0] + dx, cur_pos[1] + dy

            # Kiểm tra vị trí mới có hợp lệ không
            if is_valid(new_x, new_y, maze):
                new_pos = (new_x, new_y)
                new_stones = list(cur_stones)

                # Nếu Ares gặp viên đá
                if new_pos in cur_stones:
                    idx = cur_stones.index(new_pos) # Lấy index của viên đá
                    stone_new_x, stone_new_y = new_x + dx, new_y + dy
                    if is_valid(stone_new_x, stone_new_y, maze) and (stone_new_x, stone_new_y) not in cur_stones:
                        # if is_deadlock(maze, stones, switches, (stone_new_x, stone_new_y), new_pos, deadlocks):
                        #     continue
                        if deadfield[stone_new_x][stone_new_y] not in ('V','.'):
                            continue
                        new_stones[idx] = (stone_new_x, stone_new_y)
                        tmp_walls = []
                        if new_stones[idx] not in switches and vertical_normal_block(maze, new_stones[idx], new_stones, tmp_walls, deadfield) and horizontal_normal_block(maze, new_stones[idx], new_stones, tmp_walls, deadfield):
                            continue 
                        total_weight += weights[idx]
                        move_char = char.upper() # Đẩy đá -> in hoa
                    else:
                        continue # Không thể đẩy viên đá, bỏ qua bước này
                else:
                    move_char = char # Chỉ di chuyển Ares -> chữ thường

                state = (new_pos, tuple(new_stones))
                if state not in visited:
                    visited.add(state)
                    queue.append((new_pos, new_stones, path + move_char, total_weight))
                    node_count += 1

    end_time = time.time()
    end_memory = psutil.Process(os.getpid()).memory_info().rss
    memory_used = (end_memory - start_memory) / (1024 * 1024)
    return {
        'steps': "No solution",
        'weight': total_weight,
        'nodes': node_count,
        'time': (end_time - start_time) * 1000,
        'memory': memory_used,
        'path': path
    }

# Thuật toán IDDFS
def iddfs(maze, ares, stones, switches, weights, deadfield):
    tracemalloc.start()
    start_time = time.time()
    depth_limit = 0
    node_count = 0
    total_weight = 0
    while True:
        
        result, path, total_weight, new_node_count = dls(maze,ares, stones, switches,weights, depth_limit, deadfield)
        node_count += new_node_count
        
        if result:
            end_time = time.time()
            _, peak_memory = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            memory_used = peak_memory / (1024 * 1024)
            return {
                'steps': len(path),
                'weight': total_weight,
                'nodes': node_count,
                'time': (end_time - start_time) * 1000,
                'memory': memory_used,
                'path': path
            }

        # if result is False:
        #     return "No solution", 0, node_count
        
        depth_limit += 1        

# Thuật toán DFS
def dls(maze, ares, stones, switches, weights, depth_limit, deadfield):
    initial_state = (ares, tuple(stones), "", 0, 0)
    stack = [initial_state]
    visited = set()
    node_count = 0
    total_weight = 0
    
    while stack:
        # Lấy trạng thái hiện tại từ stack
        cur_ares, cur_stones, path, effort, depth = stack.pop()
        ares_x, ares_y = cur_ares

        # Nếu tất cả viên đá đã ở đúng vị trí
        if is_goal_state(cur_stones, switches):
            return True, path, total_weight, node_count
        
        if depth >= depth_limit:
            continue        

        # Duyệt qua các hướng đi có thể
        for (dx, dy), char in DIRECTIONS:
            new_ares_x, new_ares_y = ares_x + dx, ares_y + dy
            new_ares = (new_ares_x, new_ares_y)

            # Kiểm tra tính hợp lệ của vị trí mới của Ares
            if not is_valid(new_ares_x, new_ares_y, maze):
                continue

            # Tạo một bản sao của cur_stones để cập nhật
            new_stones = list(cur_stones)
            new_path = path
            new_effort = effort

            # Kiểm tra xem Ares có gặp viên đá không
            if new_ares in cur_stones:
                idx = new_stones.index(new_ares)
                new_stone_x, new_stone_y = new_ares_x + dx, new_ares_y + dy
                new_stone = (new_stone_x, new_stone_y)

                # Kiểm tra tính hợp lệ của vị trí mới của viên đá
                if not (is_valid(new_stone_x, new_stone_y, maze) and new_stone not in cur_stones):
                    continue
                
                if deadfield[new_stone_x][new_stone_y] not in ('V','.'):
                    continue
                # Cập nhật vị trí viên đá
                new_stones[idx] = new_stone
                tmp_walls = []
                if new_stone not in switches and vertical_normal_block(maze, new_stone, new_stones, tmp_walls, deadfield) and horizontal_normal_block(maze, new_stone, new_stones, tmp_walls, deadfield):
                    continue 
                new_effort += 1 + weights[idx]
                total_weight += weights[idx]
                new_path += char.upper()  # Đẩy viên đá (chữ in hoa)

            # Nếu Ares không đẩy đá, chỉ di chuyển bình thường
            else:
                new_path += char  # Di chuyển bình thường (chữ thường)
                new_effort += 1

            # Tạo trạng thái mới
            new_state = (new_ares, tuple(new_stones))

            # Nếu trạng thái mới chưa được thăm, hoặc có thể cải thiện effort
            if new_state not in visited:
                visited.add(new_state)
                stack.append((new_ares, tuple(new_stones), new_path, new_effort, depth + 1))
                node_count += 1

    return False, "No solution", 0, node_count

def ucs(maze, ares_pos, stones, switches, weights, deadfield):
    start_memory = psutil.Process(os.getpid()).memory_info().rss
    start_time = time.time()

    start_state = (ares_pos, tuple(stones), 0, "")
    visited = set()
    visited.add((ares_pos, tuple(stones)))
    pq = [(0, start_state)]
    heapq.heapify(pq)

    nodes_generated = 0

    global test_idx
    test_idx = 0

    while pq:
        cost, (ares_pos, stones, total_weight, path) = heapq.heappop(pq)
        nodes_generated += 1

        if is_goal_state(stones, switches):
            end_time = time.time()
            end_memory = psutil.Process(os.getpid()).memory_info().rss
            memory_used = (end_memory - start_memory) / (1024 * 1024)
            return {
                'steps': len(path),
                'weight': total_weight,
                'nodes': nodes_generated,
                'time': (end_time - start_time) * 1000,
                'memory': memory_used,
                'path': path
            }

        for (dr, dc), direction in DIRECTIONS:
            new_ares_pos = (ares_pos[0] + dr, ares_pos[1] + dc)
            
            if not is_valid(new_ares_pos[0], new_ares_pos[1], maze):
                continue

            if new_ares_pos in stones:
                stone_index = stones.index(new_ares_pos)
                new_stone_pos = (new_ares_pos[0] + dr, new_ares_pos[1] + dc)
                
                if is_valid(new_stone_pos[0], new_stone_pos[1], maze) and new_stone_pos not in stones:
                    if deadfield[new_stone_pos[0]][new_stone_pos[1]] not in ('V','.'):
                        continue
                    new_stones = list(stones)
                    new_stones[stone_index] = new_stone_pos
                    tmp_walls = []
                    if new_stone_pos not in switches and vertical_normal_block(maze, new_stone_pos, new_stones, tmp_walls, deadfield) and horizontal_normal_block(maze, new_stone_pos, new_stones, tmp_walls, deadfield):
                        continue 
                    new_total_weight = total_weight + weights[stones.index(new_ares_pos)]
                    new_state = (cost + weights[stone_index], (new_ares_pos, tuple(new_stones), new_total_weight, path + direction.upper()))
                    
                    if (new_ares_pos, tuple(new_stones)) not in visited:
                        visited.add((new_ares_pos, tuple(new_stones)))
                        heapq.heappush(pq, new_state)

            else:
                if (new_ares_pos, stones) not in visited:
                    visited.add((new_ares_pos, stones))
                    heapq.heappush(pq, (cost + 1, (new_ares_pos, stones, total_weight, path + direction)))
                    
    end_time = time.time()
    end_memory = psutil.Process(os.getpid()).memory_info().rss
    memory_used = (end_memory - start_memory) / (1024 * 1024)
    return {
        'steps': "No solution",
        'weight': total_weight,
        'nodes': nodes_generated,
        'time': (end_time - start_time) * 1000,
        'memory': memory_used,
        'path': path
    }


def heuristic_contribution(stones, switches, weights):
    total_cost = 0
    for stone, weight in zip(stones, weights):
        # Tìm khoảng cách tới công tắc gần nhất cho từng viên đá
        min_cost = float('inf')  # Khởi tạo khoảng cách nhỏ nhất là vô cực
        for switch in switches:
            # Tính toán khoảng cách Manhattan
            cost = abs(stone[0] - switch[0])  + abs(stone[1] - switch[1])
            min_cost = min(min_cost, cost)  # Cập nhật khoảng cách nhỏ nhất
        total_cost += min_cost * weight  # Cộng khoảng cách nhỏ nhất vào tổng chi phí

    return total_cost  # Trả về tổng chi phí heuristic

####################
# FREEZE DEADLOCK #
def horizontal_normal_block(maze, stone, stones, tmp_walls, deadfield):
    # Check for immediate horizontal block conditions
    if (
        (maze[stone[0]][stone[1] - 1] == '#' or (stone[0], stone[1] - 1) in tmp_walls) or 
        (maze[stone[0]][stone[1] + 1] == '#' or (stone[0], stone[1] + 1) in tmp_walls) or 
        (deadfield[stone[0]][stone[1] + 1] not in ('.', 'V') and 
         deadfield[stone[0]][stone[1] - 1] not in ('.', 'V'))
    ):
        return True
    
    # Recursive check on neighboring stones horizontally
    if is_valid(stone[0], stone[1] + 1, maze) and (stone[0], stone[1] + 1) in stones:
        if stone not in tmp_walls:
            tmp_walls.append(stone)
        if vertical_normal_block(maze, (stone[0], stone[1] + 1), stones, tmp_walls, deadfield):
            return True

    if is_valid(stone[0], stone[1] - 1, maze) and (stone[0], stone[1] - 1) in stones:
        if stone not in tmp_walls:
            tmp_walls.append(stone)
        if vertical_normal_block(maze, (stone[0], stone[1] - 1), stones, tmp_walls, deadfield):
            return True
    
    return False

def vertical_normal_block(maze, stone, stones, tmp_walls, deadfield):
    # Check for immediate vertical block conditions
    if (
        (maze[stone[0] - 1][stone[1]] == '#' or (stone[0] - 1, stone[1]) in tmp_walls) or 
        (maze[stone[0] + 1][stone[1]] == '#' or (stone[0] + 1, stone[1]) in tmp_walls) or 
        (deadfield[stone[0] + 1][stone[1]] not in ('.', 'V') and 
         deadfield[stone[0] - 1][stone[1]] not in ('.', 'V'))
    ):
        return True
    
    # Recursive check on neighboring stones vertically
    if is_valid(stone[0] + 1, stone[1], maze) and (stone[0] + 1, stone[1]) in stones:
        if stone not in tmp_walls:
            tmp_walls.append(stone)
        if horizontal_normal_block(maze, (stone[0] + 1, stone[1]), stones, tmp_walls, deadfield):
            return True

    if is_valid(stone[0] - 1, stone[1], maze) and (stone[0] - 1, stone[1]) in stones:
        if stone not in tmp_walls:
            tmp_walls.append(stone)
        if horizontal_normal_block(maze, (stone[0] - 1, stone[1]), stones, tmp_walls, deadfield):
            return True

    return False           
# FREEZE DEADLOCK #
###################

###################
# SIMPLE DEADLOCK #
def make_clone_maze(maze):
    clone_maze = copy.deepcopy(maze)
    for i, row in enumerate(clone_maze):
        for j, cell in enumerate(row):
            if cell in ('*', '+'):
                clone_maze[i][j] = '.'
            elif cell in ('@', '$'):
                clone_maze[i][j] = ' '

    return clone_maze

def print_maze_to_file(maze, new_stone_pos, stones=[], filename="maze_output.txt"):
    # Create a temporary copy of the maze to mark stones
    temp_maze = [list(row) for row in maze]  # Deep copy to avoid modifying the original maze
    
    # Mark each stone position with a symbol, e.g., 'S' for stone
    for stone in stones:
        temp_maze[stone[0]][stone[1]] = 'S'  # Place an 'S' where stones are located

    # Write the maze with stones to the file in append mode
    with open(filename, "a") as file:
        file.write(str(new_stone_pos) + '\n')
        for row in temp_maze:
            file.write("".join(row) + "\n")
        file.write("\n")  # Separate entries with a blank line
    
def pull_the_box(maze, clone_maze, switch, switches):
    q = Queue()
    q.put(switch)
    while not q.empty():
        pos = q.get()
        if pos not in switches:
            clone_maze[pos[0]][pos[1]] = 'V'
        for (dr,dc), _ in DIRECTIONS:
            new_r = dr + pos[0]
            new_c = dc + pos[1]
            if (not is_valid(new_r, new_c, maze)) or (not is_valid(new_r + dr, new_c + dc, maze)):
                continue
            if clone_maze[new_r][new_c] != 'V' and (new_r, new_c) not in switches:
                q.put((new_r, new_c))


def simple_deadlock(maze, switches):
    clone_maze = make_clone_maze(maze)
    
    for switch in switches:
        pull_the_box(maze, clone_maze, switch, switches)
        
    return clone_maze
# SIMPLE DEADLOCK #
###################

def movement_cost(maze, ares_pos, stones, switches, weights, move_i, move_j, deadfield):
    ares_new_pos = (ares_pos[0] + move_i, ares_pos[1] + move_j)

    # Check if Ares collides with a wall
    if not is_valid(ares_new_pos[0], ares_new_pos[1], maze):
        return -1  # Collision with wall

    # If Ares is moving into an empty space
    if ares_new_pos not in stones:  # Ares is moving into empty space
        return 1  # Moving cost into empty space

    # If Ares is pushing a stone
    # Calculate the position of the stone that will be pushed
    stone_new_pos = (ares_new_pos[0] + move_i, ares_new_pos[1] + move_j)

    # Check if the position to push the stone is valid
    if not is_valid(stone_new_pos[0], stone_new_pos[1], maze):
        return -1  # Invalid move, can't push the stone into a wall

    # If the new position is occupied by another stone or a wall, return -1
    if stone_new_pos in stones:
        return -1  # Can't push another stone
    
    if deadfield[stone_new_pos[0]][stone_new_pos[1]] not in ('V','.'):
        return -1

    for index in range(0, len(stones)):
        if stones[index] == ares_new_pos:
            # If the stone can be moved to the new position
            return weights[index]  # Return the weight of the stone being pushed
        
    return -1

def astar(maze, ares, stones, switches, weights, deadfield):
    start_memory = psutil.Process(os.getpid()).memory_info().rss
    start_time = time.time()
    
    initial_state = (ares, tuple(stones))
    state_space = []
    came_from = {}
    node_cnt = 0
    g_score = {initial_state: heuristic_contribution(stones, switches, weights)}
    
    heapq.heappush(state_space, (heuristic_contribution(stones, switches, weights), (initial_state)))
    while state_space:
        _, state = heapq.heappop(state_space)
        ares, stones = state[0], list(state[1])
        node_cnt +=1
        
        # Đảm bảo g_score có giá trị cho trạng thái hiện tại
        if state not in g_score:
            g_score[state] = float('inf')  # Nếu không có, khởi tạo với giá trị vô cực
        # Kiểm tra nếu đã đến đích
        if all(stone in switches for stone in stones):
            path = []
            while state in came_from:
                path.append(state)
                state = came_from[state]
            path.append(initial_state)
            path.reverse()
            return path_to_char_and_weight(start_memory, start_time, path, weights, node_cnt)
        
        for index in range(4):
            new_ares = (ares[0] + DIRECTIONS[index][0][0], ares[1] + DIRECTIONS[index][0][1])
            if not is_valid(new_ares[0], new_ares[1], maze):
                continue
            g_step = movement_cost(maze, ares, stones, switches, weights, DIRECTIONS[index][0][0], DIRECTIONS[index][0][1], deadfield)
            if g_step == -1:
                continue
            
            tentative_g = g_score[state] + g_step
            
            # Tạo một mảng mới chứa vị trí các viên đá
            new_stones = copy.deepcopy(stones)
            # Đẩy đá
            if new_ares in stones:
                # Tìm kiếm vị trí viên đá trong mảng
                stone_index = stones.index(new_ares)
                new_stone_pos = (new_ares[0] + DIRECTIONS[index][0][0], new_ares[1] + DIRECTIONS[index][0][1])
                
                # Ensure the new stone position is valid
                if not is_valid(new_stone_pos[0], new_stone_pos[1],maze) or new_stone_pos in new_stones:
                    continue 
                new_stones[stone_index] = new_stone_pos
                tmp_walls = []
                if new_stone_pos not in switches and vertical_normal_block(maze, new_stone_pos, new_stones, tmp_walls, deadfield) and horizontal_normal_block(maze, new_stone_pos, new_stones, tmp_walls, deadfield):
                    continue 
                
            
            successor = (new_ares, tuple(new_stones))
            # Kiểm tra và cập nhật g_score cho trạng thái kế tiếp
            if successor not in g_score or tentative_g < g_score[successor]:
                g_score[successor] = tentative_g  # Cập nhật g_score cho trạng thái kế tiếp
                came_from[successor] = state  # Lưu lại trạng thái trước đó
                heapq.heappush(state_space, (tentative_g + heuristic_contribution(new_stones, switches, weights), successor))  # Thêm vào danh sách mở
                
    end_time = time.time()
    end_memory = psutil.Process(os.getpid()).memory_info().rss
    memory_used = (end_memory - start_memory) / (1024 * 1024)
    return {
        'steps': len(path),
        'weight': 0,
        'nodes': node_cnt,
        'time': (end_time - start_time) * 1000,
        'memory': memory_used,
        'path': path
    }
            
def path_to_char_and_weight(start_memory, start_time, path, weights, node_cnt):
    normal_move = ['u', 'r', 'd', 'l']
    push_move = ['U', 'R', 'D', 'L']
    char_path = ""
    total_weight = 0
    for index in range(1, len(path)):
        push = path[index][0] in path[index - 1][1]
        if push:
            total_weight += weights[path[index - 1][1].index(path[index][0])]
        for j in range(4):
            if DIRECTIONS[j][0][0] == path[index][0][0] - path[index - 1][0][0] and DIRECTIONS[j][0][1] == path[index][0][1] - path[index - 1][0][1]:
                char_path += push_move[j] if push else normal_move[j]
    end_time = time.time()
    end_memory = psutil.Process(os.getpid()).memory_info().rss
    memory_used = (end_memory - start_memory) / (1024 * 1024)
    return {
        'steps': len(path) - 1,
        'weight': total_weight,
        'nodes': node_cnt,
        'time': (end_time - start_time) * 1000,
        'memory': memory_used,
        'path': char_path
    }

# Measure and log algorithm results
def log_results(output_file, algorithm, result, cnt = 1):
    output = f"{algorithm}\nSteps: {result['steps']}, Weight: {result['weight']}, Nodes: {result['nodes']}, Time (ms): {result['time']:.2f}, Memory (MB): {result['memory']:.2f}\n{result['path']}\n"
    if cnt == 1:
        with open(output_file, "w") as f:
            f.write(output)
    else:
        with open(output_file, "a") as f:
            f.write(output)

# Process each input file and generate corresponding output files
def process_files():
    input_files = sorted(f for f in os.listdir() if f.startswith("input-") and f.endswith(".txt"))

    for input_file in input_files:
        file_index = input_file.split('-')[1].split('.')[0]
        output_file = f"output-{file_index}.txt"
        
        weights, maze = load_maze(input_file)
        ares, stones, switches = find_positions(maze)

        file_deadfield = simple_deadlock(maze, switches) # Lưu các deadlock bất biến vào mảng
        cnt = 0
        for algo, func in [("BFS", bfs), ("IDDFS", iddfs), ("UCS", ucs), ("A*", astar)]:
            cnt +=1
            tracemalloc.start()
            result = func(maze, ares, stones, switches, weights, file_deadfield)
            tracemalloc.stop()

            log_results(output_file, algo, result, cnt)

# Di chuyển nhân vật và đá
def move(ares, stones, direction, maze, weights, step_count, current_weight):
    dx, dy = direction
    new_x, new_y = ares[0] + dx, ares[1] + dy

    if not is_valid(new_x, new_y, maze):
        return ares, stones, step_count, current_weight  # Không thể di chuyển

    if (new_x, new_y) in stones:
        stone_idx = stones.index((new_x, new_y))
        stone_new_x, stone_new_y = new_x + dx, new_y + dy

        if is_valid(stone_new_x, stone_new_y, maze) and (stone_new_x, stone_new_y) not in stones:
            stones[stone_idx] = (stone_new_x, stone_new_y)
            current_weight += weights[stone_idx]  # Cập nhật trọng lượng khi đẩy đá
            ares = (new_x, new_y)
            step_count += 1
    else:
        ares = (new_x, new_y)
        step_count += 1

    return ares, stones, step_count, current_weight

# Vẽ giao diện
def draw_scene(maze, ares, stones, switches, step_count, total_weight, weights, width_maze, height_maze):
    # Xóa màn hình map
    pygame.draw.rect(screen, BLACK, (0, 0, width_maze, height_maze))
    inside = inside_maze(maze, ares)
    
    for i, row in enumerate(inside):
        for j, cell in enumerate(row):
            if cell == 'V':
                screen.blit(empty_img, (j * TILE_SIZE, i * TILE_SIZE))
            
    for i, row in enumerate(maze):
        for j, cell in enumerate(row):
            if cell == '#':
                screen.blit(wall_img, (j * TILE_SIZE, i * TILE_SIZE))
            elif (i, j) in switches:
                screen.blit(switch_img, (j * TILE_SIZE, i * TILE_SIZE))

    # Vẽ Ares
    screen.blit(ares_img, (ares[1] * TILE_SIZE, ares[0] * TILE_SIZE))

     # Vẽ đá và hiển thị cân nặng của từng viên đá
    for idx, stone in enumerate(stones):
        screen.blit(stone_img, (stone[1] * TILE_SIZE, stone[0] * TILE_SIZE))
        weight_text = font.render(str(weights[idx]), True, BLACK)  # Hiển thị trọng lượng đá
        screen.blit(weight_text, (stone[1] * TILE_SIZE + TILE_SIZE // 3, stone[0] * TILE_SIZE + TILE_SIZE // 3))  # Đặt text lên viên đá

    # Hiển thị số bước và trọng lượng
    pygame.draw.rect(screen, BLACK, (10, height_maze - 40, 200, 50))
    step_text = font.render(f"Steps: {step_count}", True, WHITE)
    weight_text = font.render(f"Weight: {total_weight}", True, WHITE)  # Hiển thị trọng lượng hiện tại
    screen.blit(step_text, (10, height_maze - 40))
    screen.blit(weight_text, (10, height_maze - 10))  # Đặt text trọng lượng ở vị trí phù hợp

    pygame.display.flip()

# Hiển thị danh sách file và thuật toán
def display_file_list(file_list):
    file_width = 100
    file_height = 30
    x, y = 0, 0
    # Tính chiều rộng màn hình và độ cao màn hình dựa trên số lượng file
    screen_width = 400  # Chiều rộng tổng của màn hình
    screen_height = len(file_list) * (file_height + 10) + 20  # Chiều cao phù hợp chứa tất cả file

    # Tạo màn hình với kích thước vừa tính
    screen = pygame.display.set_mode((screen_width, screen_height))

    # Tính x để căn giữa các hình chữ nhật theo chiều ngang
    x = (screen_width - file_width) // 2

    # Vẽ danh sách các file ở giữa màn hình
    for index, file in enumerate(file_list):
        file_rect = pygame.Rect(x, y + index * (file_height + 10), file_width, file_height)
        pygame.draw.rect(screen, (200, 200, 200), file_rect)
        
        # Tạo label và tính toán kích thước của nó
        label = font.render(file, True, BLACK)
        label_width, label_height = label.get_size()
        
        # Tính toán vị trí để căn giữa chữ trong hình chữ nhật
        label_x = file_rect.x + (file_rect.width - label_width) // 2
        label_y = file_rect.y + (file_rect.height - label_height) // 2
        
        # Vẽ chữ vào giữa hình chữ nhật
        screen.blit(label, (label_x, label_y))

    
    pygame.display.flip()

def draw_control_buttons(width_maze, height_maze, pause=None):
    x_start = width_maze / 2 - (2 * TILE_SIZE)
    y_position = height_maze + 10

    pygame.draw.rect(screen, BLACK, (x_start, y_position, x_start + TILE_SIZE, y_position + TILE_SIZE))

    # Vẽ nút start hoặc pause
    if pause:
        screen.blit(pause_button, (x_start, y_position))
    else:
        screen.blit(start_button, (x_start, y_position))
    
    # Vẽ nút reset
    screen.blit(reset_button, (x_start + 2 * TILE_SIZE, y_position))

    # Vẽ nút menu
    screen.blit(menu_button, (width_maze + BUTTON_PANEL_SIZE - TILE_SIZE, 0))
    pygame.display.flip()

def draw_algorithm_buttons(width_maze, selected_algorithm=None):
    button_width = BUTTON_PANEL_SIZE - 10
    button_height = 30
    y_start = 100
    x_position = width_maze + 10  # Vị trí x cho các nút

    # Làm sạch khu vực nút trước khi vẽ
    pygame.draw.rect(screen, BLACK, (x_position, y_start, BUTTON_PANEL_SIZE, y_start + len(ALGORITHMS) * (button_height + 10) + 5))

    for index, algorithm in enumerate(ALGORITHMS):
        button_rect = pygame.Rect(x_position, y_start + index * (button_height + 10), button_width, button_height)

        # Kiểm tra xem thuật toán này có được chọn không để highlight
        if algorithm == selected_algorithm:
            color = (100, 100, 100)  # màu highlight
        else:
            color = (200, 200, 200)  # Màu bình thường (xám nhạt)

        pygame.draw.rect(screen, color, button_rect)
        label = font.render(algorithm, True, BLACK)
        screen.blit(label, (x_position + 10, y_start + index * (button_height + 10) + 5))

    pygame.display.flip()

# Bắt sự kiện khi chọn file
def check_file_click(mouse_pos, file_list):
    file_width = 100
    file_height = 30
    
    x = (400 - file_width) // 2
    y = 0

    for index, file in enumerate(file_list):
        file_rect = pygame.Rect(x, y + index * (file_height + 10), file_width, file_height)
        if file_rect.collidepoint(mouse_pos):
            click_effect.play() # Phát âm thanh khi chọn
            return file

# Bắt sự kiện khi nhấn nút
def check_button_click(mouse_pos, width_maze, height_maze):
    # Kiểm tra chọn Menu
    x = width_maze + BUTTON_PANEL_SIZE  - TILE_SIZE
    y = 0
    if x <= mouse_pos[0] <= x + TILE_SIZE and y <= mouse_pos[1] <= y + TILE_SIZE: 
        click_effect.play() # Phát âm thanh khi chọn
        return "Menu"

    # Kiểm tra nút thuật toán
    button_width = BUTTON_PANEL_SIZE - 10
    button_height = 30
    y = 100
    x = width_maze + 10

    for index, algorithm in enumerate(ALGORITHMS):
        button_rect = pygame.Rect(x, y + index * (button_height + 10), button_width, button_height)
        if button_rect.collidepoint(mouse_pos):
            click_effect.play() # Phát âm thanh khi chọn
            return algorithm

    # Kiểm tra nút start, pause, reset
    x = width_maze / 2 - (2 * TILE_SIZE)
    y = height_maze + 10

    # Kiểm tra nhấp vào nút Pause
    if x <= mouse_pos[0] <= x + TILE_SIZE and y <= mouse_pos[1] <= y + TILE_SIZE:
        click_effect.play() # Phát âm thanh khi chọn
        return "pause"
    # Kiểm tra nhấp vào nút Reset
    if x + 2 * TILE_SIZE <= mouse_pos[0] <= x + 3 * TILE_SIZE and y <= mouse_pos[1] <= y + TILE_SIZE:
        click_effect.play() # Phát âm thanh khi chọn
        return "reset"

    return None

def run_game_ui():
    global screen

    input_files = sorted(f for f in os.listdir() if f.startswith("input-") and f.endswith(".txt"))
    selected_file = None
    selected_algorithm = None
    original_maze = None  # Lưu trữ bản đồ gốc để reset
    ares, stones, switches = None, [], []
    weights = None
    width_maze, height_maze = None, None
    running = True
    pause = True  # Lưu trạng thái nút pause
    reseted = True
    checked_file = False

    while running:
        if not selected_file:
            if not checked_file:
                checked_file = True
                # Hiển thị màn hình chọn file
                screen.fill(WHITE)
                display_file_list(input_files)

            # Lặp qua sự kiện để kiểm tra xem người dùng chọn file nào
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    selected_file = check_file_click(mouse_pos, input_files)

                    if selected_file:                         
                        weights, original_maze = load_maze(selected_file)  # Lưu bản đồ gốc
                        ares, stones, switches = find_positions(original_maze)
                        gui_deadfield = simple_deadlock(original_maze, switches) # Lưu các deadlock bất biến vào mảng
                        width_maze, height_maze = calculate_window_size(original_maze)
                        height_maze += 40
                        screen = pygame.display.set_mode((width_maze + BUTTON_PANEL_SIZE, height_maze + BUTTON_PANEL_SIZE + 10))
                        draw_algorithm_buttons(width_maze, selected_algorithm)  # Vẽ nút
                        draw_scene(original_maze, ares, stones, switches, 0, 0, weights, width_maze, height_maze)
                        draw_control_buttons(width_maze, height_maze, pause)
                        checked_file = False    # Đặt lại checked_file

        else:
            # Màn hình chờ chọn thuật toán hoặc xử lý thuật toán
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    result = check_button_click(mouse_pos, width_maze, height_maze)

                    if result == "Menu":
                        selected_file = None  # Quay lại màn hình chọn file
                        selected_algorithm = None
                        pause = True
                    elif result in ALGORITHMS:
                        pause = False
                        selected_algorithm = result  # Lưu thuật toán đã chọn
                        print(f"Selected algorithm: {selected_algorithm}")

                        # Reset lại trạng thái bản đồ ban đầu
                        ares, stones, switches = find_positions(original_maze)  # Tìm vị trí mới

                        # Vẽ lại giao diện với nút được highlight
                        draw_scene(original_maze, ares, stones, switches, 0, 0, weights, width_maze, height_maze)
                        draw_algorithm_buttons(width_maze, selected_algorithm)  # Cập nhật highlight
                        draw_control_buttons(width_maze, height_maze, pause)

                        # Bắt đầu chạy thuật toán
                        result = search_algorithm(selected_algorithm, original_maze, ares, stones, switches, weights, gui_deadfield)
                        path = result['path']
                        
                        run_algorithm(path, original_maze, ares, stones, switches, weights, width_maze, height_maze)  # Chạy thuật toán
                        reseted  = False
                        # Cập nhật nút điều khiển khi chạy xong
                        pause = True
                        draw_control_buttons(width_maze, height_maze, pause)

                    elif result == "reset":
                        reseted = True
                        pause = True
                        # Thiết lập lại tất cả các biến liên quan đến bản đồ
                        ares, stones, switches = find_positions(original_maze)  # Đặt lại vị trí của Ares, đá và công tắc
                        step_count = 0
                        current_weight = 0
                        
                        # Vẽ lại giao diện với bản đồ gốc
                        draw_scene(original_maze, ares, stones, switches, step_count, current_weight, weights, width_maze, height_maze)
                        
                        # Cập nhật các nút điều khiển
                        draw_control_buttons(width_maze, height_maze, pause)  # Vẽ lại các nút điều khiển
                        pygame.display.flip()  # Cập nhật màn hình

                    elif result == "pause" and selected_algorithm and reseted:
                        pause = not pause
                        draw_control_buttons(width_maze, height_maze, pause)
                        run_algorithm(path, original_maze, ares, stones, switches, weights, width_maze, height_maze)  # Chạy thuật toán
                        # Cập nhật các nút điều khiển
                        pause = True
                        draw_control_buttons(width_maze, height_maze, pause)
                        reseted = False

    pygame.quit()



def run_algorithm(path, maze, ares, stones, switches, weights, width_maze, height_maze):
    """Chạy thuật toán và di chuyển Ares."""
    step_count = 0
    path_index = 0
    current_weight = 0
    pause = False
    running = True


    while running and path_index < len(path):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    result = check_button_click(mouse_pos, width_maze, height_maze)

                    if result == "pause":
                        pause = not pause
                        draw_control_buttons(width_maze, height_maze, pause)
                        
                    elif result == "reset":
                        ares, stones, switches = find_positions(maze)
                        step_count = 0
                        path_index = 0
                        current_weight = 0

                        # Vẽ lại giao diện với bản đồ gốc
                        draw_scene(maze, ares, stones, switches, step_count, current_weight, weights, width_maze, height_maze)
                        draw_control_buttons(width_maze, height_maze, pause)  # Vẽ lại các nút điều khiển
                        walk_effect.play()

        if not pause and path_index < len(path):
            direction = get_direction_from_char(path[path_index])
            ares, stones, step_count, current_weight = move(ares, stones, direction, maze, weights, step_count, current_weight)
            draw_scene(maze, ares, stones, switches, step_count, current_weight, weights, width_maze, height_maze)
            walk_effect.play()
            path_index += 1
        
        pygame.display.flip()
        time.sleep(0.1)

def get_direction_from_char(char):
    if char in 'Uu':
        return -1, 0
    elif char in 'Dd':
        return 1, 0
    elif char in 'Ll':
        return 0, -1
    elif char in 'Rr':
        return 0, 1
    return 0, 0

if __name__ == "__main__":
    # Tạo và bắt đầu luồng cho process_files
    file_thread = threading.Thread(target=process_files)
    file_thread.start()
    
    # Chạy run_game_ui trên luồng chính
    run_game_ui()
    
    # Đợi luồng file_thread hoàn tất (nếu cần thiết)
    file_thread.join()