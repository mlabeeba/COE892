'''
Lab 1 - Part 1 [ Threads ]
'''

import requests
import time
import os
import threading

# Function: Reads map.txt
# --
def read_map(file_path):
    with open(file_path, 'r') as file:
        dimensions = file.readline().strip().split()
        rows, cols = int(dimensions[0]), int(dimensions[1])
        map_data = [file.readline().strip().split() for _ in range(rows)]
    return rows, cols, map_data

# Function: Returns location of mines as (x, y) as an array
# --
def get_mines(map_data):
    mine_locations = []                                     # Stores mine locations into an array
    for r_index, row in enumerate(map_data):                # Parse through map.txt
        for c_index, value in enumerate(row):
            if value == '1':                                # If value of map.txt = 1
                mine_locations.append((c_index, r_index))   # Store mine value as (x, y)
    return mine_locations

# Function: Get rover commands from API
# --
def get_rover_commands(rover_num):
    url = f"https://coe892.reev.dev/lab1/rover/{rover_num}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['data']['moves']
    elif response.status_code == 404:
        return None

# Function: Navigate through the maop
# --
def get_rover_path(map_data, commands, mine_locations, lock):
    direction = 'S'         # Rover starts facing South ...
    pos = [0, 0]            # ... @ location (0, 0) on map

    directions = {'N': [0, -1], 'S': [0, 1], 'E': [1, 0], 'W': [-1, 0]}     # Define rovers directions
    turn_left = {'N': 'W', 'E': 'N', 'W': 'S', 'S': 'E'}                    # Define library for when the rover turns left
    turn_right = {'N': 'E', 'E': 'S', 'S': 'W', 'W': 'N'}                   # Define library for when the rover turns right

    path = [['0' for _ in range(len(map_data[0]))] for _ in range(len(map_data))]       # Create 2D list initialized with '0's
    path[pos[1]][pos[0]] = '*'                                                          # Mark position of rover with '*'s
    mine_hit = False

    for i, command in enumerate(commands):

        # Left Turn
        if command == 'L':
            direction = turn_left[direction]

        # Right Turn
        elif command == 'R':
            direction = turn_right[direction]

        # Move Forward
        elif command == 'M':

            # Calculate new (x, y) positions based on current direction
            new_x = pos[0] + directions[direction][0]
            new_y = pos[1] + directions[direction][1]

            # If new position is within the map grid
            if 0 <= new_x < len(map_data[0]) and 0 <= new_y < len(map_data):
                pos[0], pos[1] = new_x, new_y           # Update current position w/ new position
                path[pos[1]][pos[0]] = '*'              # Mark new position with '*'

                # If new position is on a mine
                if (pos[0], pos[1]) in mine_locations:
                    mine_hit = True         # Change flag to true

                    # If the new command is not dig 'D', break
                    if not (i + 1 < len(commands) and commands[i + 1] == 'D'):
                        break
                    '''
                    if i + 1 < len(commands) and commands[i + 1] == 'D':
                        print(f"Mine detected at {pos[0]}, {pos[1]}, waiting for disarm.")
                    else:
                        print(f"Mine detected at {pos[0]}, {pos[1]}, stopping movement.")
                        break
                    '''

        # Dig
        elif command == 'D' and mine_hit and (pos[0], pos[1]) in mine_locations:
            with lock:                                      # Use 'lock' to ensure that shared data can be safely modified
                mine_locations.remove((pos[0], pos[1]))     # Remove the mine safely using lock
            mine_hit = False                                # Reset the 'mine_hit' flag

    return path

# Function: Save Rover's Path as a text file
# --
def save_path(rover_id, path):
    directory = "rover_paths"
    os.makedirs(directory, exist_ok=True)
    file_name = os.path.join(directory, f"path_{rover_id}.txt")
    with open(file_name, 'w') as file:
        for row in path:
            file.write(" ".join(row) + "\n")

# Function: Execute rover and save path
# --
def execute_rover(rover_id, map_data, mine_locations, lock):
    commands = get_rover_commands(rover_id)
    if commands:
        rover_path = get_rover_path(map_data, commands, mine_locations, lock)
        save_path(rover_id, rover_path)

# Main function
# --
def main():
    file_path = 'map1.txt'
    rows, cols, map_data = read_map(file_path)
    mine_locations = get_mines(map_data)

    start_time = time.time()    # Start Executing

    threads = []                    # Threading object created
    lock = threading.Lock()         # Lock object created

    for rover_id in range(1, 11):
        # Create a thread and pass the 'execute_rover' function as the target without calling it
        thread = threading.Thread(target=execute_rover, args=(rover_id, map_data, mine_locations[:], lock))
        threads.append(thread)
        thread.start()

    for thread in threads:          # Ensures that the main program waits for all  ...
        thread.join()               # ... threads to complete before continuing

    end_time = time.time()      # Stop Executing

    execution_time = end_time - start_time
    print(f"Total execution time: {execution_time:.2f} seconds")

if __name__ == "__main__":
    main()

