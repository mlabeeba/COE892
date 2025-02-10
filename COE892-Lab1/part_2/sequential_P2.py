import requests
import hashlib
import time


def read_map(file_path):
    with open(file_path, 'r') as file:
        dimensions = file.readline().strip().split()
        rows, cols = int(dimensions[0]), int(dimensions[1])
        map_data = [file.readline().strip().split() for _ in range(rows)]
    return rows, cols, map_data


def fetch_rover_commands(rover_id):
    url = f"https://coe892.reev.dev/lab1/rover/{rover_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['data']['moves']
    else:
        print(f"Error fetching commands for Rover {rover_id}: {response.status_code}")
        return None


def read_mine_serials(serial_file):
    with open(serial_file, 'r') as file:
        serial_numbers = [line.strip() for line in file.readlines()]
    return serial_numbers


def find_valid_pin(serial_number):
    trial = 0
    while True:
        # Generating a candidate PIN by appending the trial number to 'PIN'
        candidate_pin = f'PIN{trial}'
        temp_mine_key = candidate_pin + serial_number
        hashed_key = hashlib.sha256(temp_mine_key.encode()).hexdigest()
        # Check if the hash has at least six leading zeros
        if hashed_key.startswith('000000'):
            print(f"Valid PIN found: {candidate_pin}, Hash: {hashed_key}")
            return candidate_pin
        trial += 1


def simulate_rover_movement(map_data, commands, serial_numbers):
    direction = 'S'  # Start facing South
    pos = [0, 0]  # (x, y)
    directions = {'N': [0, -1], 'S': [0, 1], 'E': [1, 0], 'W': [-1, 0]}
    turn_left = {'N': 'W', 'W': 'S', 'S': 'E', 'E': 'N'}
    turn_right = {'N': 'E', 'E': 'S', 'S': 'W', 'W': 'N'}
    serial_index = 0  # Track the next serial number to assign

    print(f"Initial Position: {pos}, Facing: {direction}")

    for command in commands:
        if command == 'L':
            direction = turn_left[direction]
            print(f"Turn Left, Now Facing: {direction}")
        elif command == 'R':
            direction = turn_right[direction]
            print(f"Turn Right, Now Facing: {direction}")
        elif command == 'M':
            new_x = pos[0] + directions[direction][0]
            new_y = pos[1] + directions[direction][1]
            if 0 <= new_x < len(map_data[0]) and 0 <= new_y < len(map_data):
                pos[0], pos[1] = new_x, new_y
                print(f"Move to: {pos}")
                if map_data[pos[1]][pos[0]] == '1':
                    if serial_index < len(serial_numbers):
                        serial_number = serial_numbers[serial_index]
                        print(f"Warning: Rover is now on a mine at {pos}. Serial number: {serial_number}")
                        valid_pin = find_valid_pin(serial_number)
                        map_data[pos[1]][pos[0]] = '0'  # Disarm the mine and clear the spot
                        serial_index += 1
                    else:
                        print(f"Warning: Rover is on a mine at {pos}, but no more serial numbers are available.")
            else:
                print("Move ignored, out of bounds")
        elif command == 'D':
            if map_data[pos[1]][pos[0]] == '1':
                serial_number = serial_numbers[serial_index]
                print(f"Dig at {pos}: Mine found. Serial number: {serial_number}")
                valid_pin = find_valid_pin(serial_number)
                map_data[pos[1]][pos[0]] = '0'  # Disarm the mine and clear the spot
                serial_index += 1
            else:
                print(f"Dig at {pos}: No mine found.")


def main():
    start_time = time.time()  # Start timing

    map_file_path = 'map1.txt'  # Ensure the file path is correct and accessible
    serial_file_path = 'mines.txt'  # Ensure the file path is correct and accessible
    rows, cols, map_data = read_map(map_file_path)
    serial_numbers = read_mine_serials(serial_file_path)

    # Fetch commands only for Rover 1
    commands = fetch_rover_commands(1)
    if commands:
        simulate_rover_movement(map_data, commands, serial_numbers)
    else:
        print("No commands received for Rover 1")

    end_time = time.time()  # End timing
    print(f"Total execution time: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    main()
