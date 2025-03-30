
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import random
import string
import os
import json
import requests
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


from Utils.map_mine_utils import (
    map_data,
    MapDimensions,
    Coord,
    load_map,
    save_map,
    mines,
    Mine,
    UpdateMine,
    read_map
)
from Utils.rover_utils import (
    NewRover,
    RoverUpdate,
)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/dashboard.html")

# Allow frontend JS fetch to work
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def serve_dashboard():
    return FileResponse("static/dashboard.html")


@app.on_event("startup")
def startup():
    load_map()


# ------------------------
# MAP SECTION
# ------------------------
@app.get("/map")
def get_map():
    return read_map()

@app.put("/map")
def update_map(dim: MapDimensions):
    old_grid = map_data.get("grid", [])
    old_height = len(old_grid)
    old_width = len(old_grid[0]) if old_height > 0 else 0

    new_grid = [[0 for _ in range(dim.width)] for _ in range(dim.height)]

    # Copy existing bombs into new grid where possible
    for i in range(min(dim.height, old_height)):
        for j in range(min(dim.width, old_width)):
            new_grid[i][j] = old_grid[i][j]

    map_data["height"] = dim.height
    map_data["width"] = dim.width
    map_data["grid"] = new_grid

    # Save to file
    with open("map1.txt", "w") as f:
        f.write(f"{dim.height} {dim.width}\n")
        for row in new_grid:
            f.write(" ".join(map(str, row)) + "\n")

    return {"status": "success", "message": "Map resized and saved"}

@app.post("/map/toggle-mine")
def toggle_mine(coord: Coord):
    x, y = coord.x, coord.y
    if 0 <= x < map_data["height"] and 0 <= y < map_data["width"]:
        map_data["grid"][x][y] = 1 - map_data["grid"][x][y]
        save_map()
        return {"status": "success"}
    raise HTTPException(status_code=400, detail="Invalid coordinates")

# ------------------------
# MINE SECTION
# ------------------------
@app.get("/mines")
def get_mines():
    return mines

@app.get("/mines/{mine_id}")
def get_mine(mine_id: int):
    for mine in mines:
        if mine["id"] == mine_id:
            return mine
    raise HTTPException(status_code=404, detail="Mine not found")

@app.post("/mines")
def create_mine(mine: Mine):
    global mine_id_counter
    mine.id = mine_id_counter
    mine_id_counter += 1
    mines.append(mine.dict())
    map_data["grid"][mine.x][mine.y] = 1
    save_map()
    return {"id": mine.id}

@app.put("/mines/{mine_id}")
def update_mine(mine_id: int, mine_update: UpdateMine):
    for mine in mines:
        if mine["id"] == mine_id:
            if mine_update.x is not None:
                mine["x"] = mine_update.x
            if mine_update.y is not None:
                mine["y"] = mine_update.y
            if mine_update.serial_number is not None:
                mine["serial_number"] = mine_update.serial_number
            save_map()
            return mine
    raise HTTPException(status_code=404, detail="Mine not found")

@app.delete("/mines/{mine_id}")
def delete_mine(mine_id: int):
    for i, mine in enumerate(mines):
        if mine["id"] == mine_id:
            x, y = mine["x"], mine["y"]
            map_data["grid"][x][y] = 0
            save_map()
            del mines[i]
            return {"message": "Mine deleted"}
    raise HTTPException(status_code=404, detail="Mine not found")

@app.post("/dig")
async def dig_mine(request: Request):
    data = await request.json()
    x, y = data.get("x"), data.get("y")

    grid = read_map()["grid"]

    with open("mines.txt", "r") as f:
        mine_serials = [line.strip() for line in f.readlines()]

    coord_to_serial = {}
    idx = 0
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            if grid[i][j] > 0 and idx < len(mine_serials):
                coord_to_serial[(i, j)] = mine_serials[idx]
                idx += 1

    serial = coord_to_serial.get((x, y))
    if not serial:
        print(f"❌ No mine found at ({x}, {y})")
        return {"success": False, "message": "No mine at this location."}

    print(f"🧨 Disarming mine at ({x}, {y}) with serial {serial}")

    while True:
        pin = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        hash_val = hashlib.sha256(f"{serial}{pin}".encode()).hexdigest()
        if hash_val.startswith("000000"):
            break

    print(f"✅ PIN found: {pin} (Hash: {hash_val})")
    return {"success": True, "pin": pin, "serial": serial}

# ------------------------
# ROVER SECTION
# ------------------------
@app.get("/fetch-rovers")
def fetch_and_save_rovers():
    base_url = "https://coe892.reev.dev/lab1/rover/"
    rover_data = []

    try:
        os.makedirs("rover_info", exist_ok=True)

        with open("rover_info/rover_data.txt", "w") as f:
            for i in range(1, 11):
                url = f"{base_url}{i}"
                response = requests.get(url)

                if response.status_code == 200:
                    payload = response.json()
                    if payload.get("result") and "data" in payload:
                        rover_entry = {
                            "id": i,
                            "moves": payload["data"]["moves"]
                        }
                        rover_data.append(rover_entry)
                        f.write(json.dumps(rover_entry) + "\n")
                        print(f"✅ Saved rover {i}")
                    else:
                        print(f"⚠️ Invalid response for rover {i}: {payload}")
                else:
                    print(f"❌ Failed to fetch rover {i}: {response.status_code}")

        return {
            "status": "success",
            "message": f"{len(rover_data)} rovers saved to rover_info/rover_data.txt"
        }

    except Exception as e:
        print(f"❗ Error: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/rovers")
def get_rovers():
    try:
        with open("rover_info/rover_data.txt", "r") as f:
            return [json.loads(line.strip()) for line in f if line.strip()]
    except Exception as e:
        print("Error loading rover data:", e)
        return []

@app.post("/rovers/update")
async def update_rover(update: RoverUpdate):
    try:
        with open("rover_info/rover_data.txt", "r") as f:
            rovers = [json.loads(line.strip()) for line in f if line.strip()]

        if 0 <= update.index < len(rovers):
            rovers[update.index]["id"] = update.id
            rovers[update.index]["moves"] = update.moves

            with open("rover_info/rover_data.txt", "w") as f:
                for rover in rovers:
                    f.write(json.dumps(rover) + "\n")

            return {"status": "success"}
        else:
            return {"status": "error", "message": "Invalid index"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.delete("/rovers/{index}")
def delete_rover(index: int):
    try:
        with open("rover_info/rover_data.txt", "r") as f:
            rovers = [json.loads(line.strip()) for line in f if line.strip()]
        if 0 <= index < len(rovers):
            del rovers[index]
            with open("rover_info/rover_data.txt", "w") as f:
                for rover in rovers:
                    f.write(json.dumps(rover) + "\n")
            return {"status": "success"}
        else:
            return {"status": "error", "message": "Invalid index"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/rovers/create")
def create_rover(rover: NewRover):
    try:
        with open("rover_info/rover_data.txt", "r") as f:
            rovers = [json.loads(line.strip()) for line in f if line.strip()]

        if any(r["id"] == rover.id for r in rovers):
            return {"status": "error", "message": "Rover ID already exists"}

        rovers.append({"id": rover.id, "moves": rover.moves})

        with open("rover_info/rover_data.txt", "w") as f:
            for r in rovers:
                f.write(json.dumps(r) + "\n")

        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
