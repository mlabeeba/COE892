import hashlib
import random
import string
from typing import Optional
from pydantic import BaseModel

MAP_FILE = "map1.txt"
MINES_FILE = "mines.txt"

# ------------------------
# DATA MODELS
# ------------------------
class MapDimensions(BaseModel):
    height: int
    width: int

class Coord(BaseModel):
    x: int
    y: int

class Mine(BaseModel):
    id: int
    x: int
    y: int
    serial_number: str

class UpdateMine(BaseModel):
    x: Optional[int] = None
    y: Optional[int] = None
    serial_number: Optional[str] = None

# ------------------------
# GLOBAL STATE
# ------------------------
map_data = {
    "height": 0,
    "width": 0,
    "grid": []
}

mines = []
mine_id_counter = 1

# ------------------------
# MAP FUNCTIONS
# ------------------------
def load_map():
    with open("map1.txt", "r") as f:
        lines = f.readlines()
        h, w = map(int, lines[0].split())
        grid = [list(map(int, line.strip().split())) for line in lines[1:]]
        map_data["height"] = h
        map_data["width"] = w
        map_data["grid"] = grid

def save_map():
    with open("map1.txt", "w") as f:
        f.write(f"{map_data['height']} {map_data['width']}\n")
        for row in map_data["grid"]:
            f.write(" ".join(map(str, row)) + "\n")


def read_map():
    with open("map1.txt", "r") as f:
        lines = f.readlines()
    height, width = map(int, lines[0].strip().split())
    grid = [list(map(int, line.strip().split())) for line in lines[1:]]
    return {"height": height, "width": width, "grid": grid}

def find_valid_pin(serial):
    while True:
        pin = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        temp_key = f"{serial}{pin}".encode()
        if hashlib.sha256(temp_key).hexdigest().startswith("000000"):
            return pin