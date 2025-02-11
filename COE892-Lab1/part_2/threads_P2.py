'''
Lab 1 - Part 2 [ Threads ]
'''

import requests
import hashlib
import time
import threading

# Function: Reads map.txt
# --
def read_map(file_path):
    with open(file_path, 'r') as file:
        dimensions = file.readline().strip().split()
        rows, cols = int(dimensions[0]), int(dimensions[1])
        map_data = [file.readline().strip().split() for _ in range(rows)]
    return rows, cols, map_data

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

# Function: Read mine serial numbers from mine.txt
# --
def read_mine_serials(serial_file):
    with open(serial_file, 'r') as file:
        serial_numbers = [line.strip() for line in file.readlines()]
    return serial_numbers

# Function: Finds a valid pin using SHA256
# --
def valid_pin_finder(serial_number):
    trial = 0  # Initialize trial number
    while True:
        candidate_pin = f'PIN{trial}'  # Generate a candidate PIN
        temp_mine_key = candidate_pin + serial_number  # Combine pin with serial number
        hashed_key = hashlib.sha256(temp_mine_key.encode()).hexdigest()  # Compute SHA256 hash
        if hashed_key.startswith('000000'):
            print(f"Valid PIN found: {candidate_pin}, Hash: {hashed_key}")
            return candidate_pin
        trial += 1

# Function: Navigate through the map
# --
def get_rover_path(map_data, commands, serial_numbers, lock, rover_id):
    direction = 'S'  # Initialize rover's direction facing South
    pos = [0, 0]     # Initial position of the rover on the map

    # Direction mappings for navigation
    directions = {'N': [0, -1], 'S': [0, 1], 'E': [1, 0], 'W': [-1, 0]}
    turn_left = {'N': 'W', 'E': 'N', 'W': 'S', 'S': 'E'}
    turn_right = {'N': 'E', 'E': 'S', 'S': 'W', 'W': 'N'}

    serial_index = 0  # Index to track the serial number of mines
    print(f"Initial Position: {pos}, Facing: {direction}")

    for command in commands:

        # Turn Left
        if command == 'L':
            direction = turn_left[direction]

        # Turn right
        elif command == 'R':
            direction = turn_right[direction]

        # Move Forward
        elif command == 'M':

            # Calculate new position based on the current direction
            new_x = pos[0] + directions[direction][0]
            new_y = pos[1] + directions[direction][1]

            # Check if new position is within the bounds of the map
            if 0 <= new_x < len(map_data[0]) and 0 <= new_y < len(map_data):
                pos[0], pos[1] = new_x, new_y  # Update rover position

                # Locking mechanism to ensure safe access to shared resources
                with lock:
                    # Check if the rover has landed on a mine
                    if map_data[pos[1]][pos[0]] == '1' and serial_index < len(serial_numbers):
                        serial_number = serial_numbers[serial_index]
                        valid_pin = valid_pin_finder(serial_number)  # Attempt to disarm the mine
                        map_data[pos[1]][pos[0]] = '0'               # Disarm the mine and clear the spot
                        serial_index += 1                            # Move to the next serial number

        # Dig
        elif command == 'D':
            with lock:
                # Check if the rover's current position has a mine
                if map_data[pos[1]][pos[0]] == '1' and serial_index < len(serial_numbers):
                    serial_number = serial_numbers[serial_index]
                    valid_pin = valid_pin_finder(serial_number)     # Disarm the mine
                    map_data[pos[1]][pos[0]] = '0'                  # Clear the spot
                    serial_index += 1                               # Increment serial number index

# Function: Main function
# --
def main():
    start_time = time.time()  # Start Executing
    lock = threading.Lock()

    map_file_path = 'map1.txt'
    serial_file_path = 'mines.txt'
    rows, cols, map_data = read_map(map_file_path)
    serial_numbers = read_mine_serials(serial_file_path)

    threads = []        # New threads object
    rover_ids = [1]     # Rover id set to 1

    for rover_id in rover_ids:
        commands = get_rover_commands(rover_id)
        if commands:
            # Create a thread and pass the 'execute_rover' function as the target without calling it
            thread = threading.Thread(target=get_rover_path, args=(map_data, commands, serial_numbers, lock, rover_id))
            threads.append(thread)
            thread.start()

    for thread in threads:  # Ensures that the main program waits for all  ...
        thread.join()  # ... threads to complete before continuing

    end_time = time.time()  # Stop Executing
    print(f"Total execution time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
