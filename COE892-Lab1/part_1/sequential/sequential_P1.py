import requests
import time
import os

# Read map.txt
# --
def read_map(file_path):
    with open(file_path, 'r') as file:
        dimensions = file.readline().strip().split()
        rows, cols = int(dimensions[0]), int(dimensions[1])
        map_data = [file.readline().strip().split() for _ in range(rows)]
    return rows, cols, map_data


def find_mines(map_data):
    mine_locations = []
    for row_index, row in enumerate(map_data):
        for col_index, value in enumerate(row):
            if value == '1':
                mine_locations.append((col_index, row_index))  # Store as (x, y)
    return mine_locations


def fetch_rover_commands(rover_id):
    url = f"https://coe892.reev.dev/lab1/rover/{rover_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['data']['moves']
    elif response.status_code == 404:
        return None
    else:
        print(f"Error fetching commands for Rover {rover_id}: {response.status_code}")
        return None


def simulate_rover_movement(map_data, commands, mine_locations):
    direction = 'S'  # Start facing South
    pos = [0, 0]  # (x, y)
    directions = {'N': [0, -1], 'S': [0, 1], 'E': [1, 0], 'W': [-1, 0]}
    turn_left = {'N': 'W', 'W': 'S', 'S': 'E', 'E': 'N'}
    turn_right = {'N': 'E', 'E': 'S', 'S': 'W', 'W': 'N'}

    path = [['0' for _ in range(len(map_data[0]))] for _ in range(len(map_data))]
    path[pos[1]][pos[0]] = '*'
    mine_hit = False

    for i, command in enumerate(commands):

        if command == 'L':
            direction = turn_left[direction]

        elif command == 'R':
            direction = turn_right[direction]

        elif command == 'M':
            new_x = pos[0] + directions[direction][0]
            new_y = pos[1] + directions[direction][1]
            if 0 <= new_x < len(map_data[0]) and 0 <= new_y < len(map_data):
                pos[0], pos[1] = new_x, new_y
                path[pos[1]][pos[0]] = '*'
                if (pos[0], pos[1]) in mine_locations:
                    mine_hit = True
                    if not (i + 1 < len(commands) and commands[i + 1] == 'D'):
                        break
                    '''
                    if i + 1 < len(commands) and commands[i + 1] == 'D':
                        print(f"Mine detected at {pos[0]}, {pos[1]}, waiting for disarm.")
                    else:
                        print(f"Mine detected at {pos[0]}, {pos[1]}, stopping movement.")
                        break
                    '''

        elif command == 'D' and mine_hit and (pos[0], pos[1]) in mine_locations:
            #print(f"Mine disarmed at {pos[0]}, {pos[1]}")
            mine_locations.remove((pos[0], pos[1]))
            mine_hit = False

    return path


def save_rover_path(rover_id, path):
    directory = "rover_paths"
    os.makedirs(directory, exist_ok=True)
    file_name = os.path.join(directory, f"path_{rover_id}.txt")
    with open(file_name, 'w') as file:
        for row in path:
            file.write(" ".join(row) + "\n")
    print(f"Path for Rover {rover_id} saved to {file_name}")


def main():
    file_path = 'map1.txt'
    rows, cols, map_data = read_map(file_path)
    mine_locations = find_mines(map_data)
    #print("Mine locations:", mine_locations)

    start_time = time.time()

    for rover_id in range(1, 11):
        commands = fetch_rover_commands(rover_id)
        if commands:
            rover_path = simulate_rover_movement(map_data, commands, mine_locations[:])
            save_rover_path(rover_id, rover_path)
        else:
            print(f"No commands received for Rover {rover_id}")

    end_time = time.time()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    main()
