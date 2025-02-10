import requests
import hashlib
import time
import threading

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
        candidate_pin = f'PIN{trial}'
        temp_mine_key = candidate_pin + serial_number
        hashed_key = hashlib.sha256(temp_mine_key.encode()).hexdigest()
        if hashed_key.startswith('000000'):
            print(f"Valid PIN found: {candidate_pin}, Hash: {hashed_key}")
            return candidate_pin
        trial += 1

def simulate_rover_movement(map_data, commands, serial_numbers, rover_id):
    direction = 'S'
    pos = [0, 0]
    directions = {'N': [0, -1], 'S': [0, 1], 'E': [1, 0], 'W': [-1, 0]}
    turn_left = {'N': 'W', 'W': 'S', 'S': 'E', 'E': 'N'}
    turn_right = {'N': 'E', 'E': 'S', 'S': 'W', 'W': 'N'}
    serial_index = 0

    print(f"Rover {rover_id} - Initial Position: {pos}, Facing: {direction}")

    for command in commands:
        if command == 'L':
            direction = turn_left[direction]
        elif command == 'R':
            direction = turn_right[direction]
        elif command == 'M':
            new_x, new_y = pos[0] + directions[direction][0], pos[1] + directions[direction][1]
            if 0 <= new_x < len(map_data[0]) and 0 <= new_y < len(map_data):
                pos[0], pos[1] = new_x, new_y
                if map_data[pos[1]][pos[0]] == '1' and serial_index < len(serial_numbers):
                    serial_number = serial_numbers[serial_index]
                    valid_pin = find_valid_pin(serial_number)
                    map_data[pos[1]][pos[0]] = '0'
                    serial_index += 1
        elif command == 'D':
            if map_data[pos[1]][pos[0]] == '1' and serial_index < len(serial_numbers):
                serial_number = serial_numbers[serial_index]
                valid_pin = find_valid_pin(serial_number)
                map_data[pos[1]][pos[0]] = '0'
                serial_index += 1

def main():
    start_time = time.time()

    map_file_path = 'map1.txt'
    serial_file_path = 'mines.txt'
    rows, cols, map_data = read_map(map_file_path)
    serial_numbers = read_mine_serials(serial_file_path)

    threads = []
    # Example with multiple rovers, here simplified as one for demonstration.
    rover_ids = [1]  # List of Rover IDs
    for rover_id in rover_ids:
        commands = fetch_rover_commands(rover_id)
        if commands:
            thread = threading.Thread(target=simulate_rover_movement, args=(map_data, commands, serial_numbers, rover_id))
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()

    end_time = time.time()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
