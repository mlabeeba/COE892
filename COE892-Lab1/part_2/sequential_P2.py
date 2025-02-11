'''
Lab 1 - Part 2 [ Sequential ]
'''

import requests
import hashlib
import time

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
    trial = 0       # Initialize trial number

    # Infinite loop until a vlid pin is found
    while True:

        candidate_pin = f'PIN{trial}'       # Concatenate 'PIN' with the trial number to generate a candidate PIN
        temp_mine_key = candidate_pin + serial_number       # Create temporary mine key by combining pin with serial number

        hashed_key = hashlib.sha256(temp_mine_key.encode()).hexdigest()     # Compute the SHA256 has
        # Check if the hash has at least six leading zeros
        if hashed_key.startswith('000000'):
            print(f"Valid PIN found: {candidate_pin}, Hash: {hashed_key}")
            return candidate_pin

        trial += 1  # Increment if hash doesn't have 6 zeros

# Function: Navigate through the maop
# --
def get_rover_path(map_data, commands, serial_numbers):
    direction = 'S'  # Rover starts facing South ...
    pos = [0, 0]  # ... @ location (0, 0) on map

    directions = {'N': [0, -1], 'S': [0, 1], 'E': [1, 0], 'W': [-1, 0]}  # Define rovers directions
    turn_left = {'N': 'W', 'E': 'N', 'W': 'S', 'S': 'E'}  # Define library for when the rover turns left
    turn_right = {'N': 'E', 'E': 'S', 'S': 'W', 'W': 'N'}

    serial_index = 0  # Track serial number
    print(f"Initial Position: {pos}, Facing: {direction}")

    for command in commands:

        # Left Turn
        if command == 'L':
            direction = turn_left[direction]
            #print(f"Turn Left, Now Facing: {direction}")

        # Right Turn
        elif command == 'R':
            direction = turn_right[direction]
            #print(f"Turn Right, Now Facing: {direction}")

        # Move Forward
        elif command == 'M':

            # Calculate new (x, y) positions based on current direction
            new_x = pos[0] + directions[direction][0]
            new_y = pos[1] + directions[direction][1]

            # If new position is within the map grid
            if 0 <= new_x < len(map_data[0]) and 0 <= new_y < len(map_data):
                pos[0], pos[1] = new_x, new_y  # Update current position w/ new position
                #print(f"Move to: {pos}")

                # If new position is on a mine
                if map_data[pos[1]][pos[0]] == '1':

                    # If there are available serial numbers
                    if serial_index < len(serial_numbers):
                        serial_number = serial_numbers[serial_index]        # Assign serial number to current mine
                        print(f"Warning: Rover is now on a mine at {pos}. Serial number: {serial_number}")
                        valid_pin = valid_pin_finder(serial_number)         # Find a valid pin to disarm mine
                        map_data[pos[1]][pos[0]] = '0'                      # Disarm the mine and clear the spot
                        serial_index += 1                                   # Increment serial number
                    else:
                        print(f"Warning: Rover is on a mine at {pos}, but no more serial numbers are available.")

        # Dig
        elif command == 'D':

            # If current position of rover is on a mine
            if map_data[pos[1]][pos[0]] == '1':
                serial_number = serial_numbers[serial_index]    # Assign a serial number for the mine
                print(f"Dig at {pos}: Mine found. Serial number: {serial_number}")
                valid_pin = valid_pin_finder(serial_number)     # Find a valid pin to disarm mine
                map_data[pos[1]][pos[0]] = '0'                  # Disarm the mine and clear the spot
                serial_index += 1                               # Increment Serial Number


# Function: Main Function
# --
def main():
    start_time = time.time()  # Start timing

    map_file_path = 'map1.txt'  # Ensure the file path is correct and accessible
    serial_file_path = 'mines.txt'  # Ensure the file path is correct and accessible
    rows, cols, map_data = read_map(map_file_path)
    serial_numbers = read_mine_serials(serial_file_path)

    # Fetch commands only for Rover 1
    commands = get_rover_commands(1)
    if commands:
        get_rover_path(map_data, commands, serial_numbers)
    else:
        print("No commands received for Rover 1")

    end_time = time.time()  # End timing

    print(f"Total execution time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
