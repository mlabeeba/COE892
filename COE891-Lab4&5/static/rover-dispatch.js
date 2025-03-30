function showSpinner() {
    document.getElementById("loadingSpinner").classList.remove("hidden");
}

function hideSpinner() {
    document.getElementById("loadingSpinner").classList.add("hidden");
}


const directions = ["N", "E", "S", "W"];
const arrows = {N: "⬆️", E: "➡️", S: "⬇️", W: "⬅️"};

function getArrow(dir) {
    return arrows[dir] || "";
}

const rover = {
    x: 0,
    y: 0,
    dir: "S",
    running: false,
    commands: [],
    commandIndex: 0,
    grid: [],
    status: "Not Started",
    pendingMine: false  // Flag for standing on a mine
};

function rotate(direction, turn) {
    let idx = directions.indexOf(direction);
    if (turn === "R") idx = (idx + 1) % 4;
    if (turn === "L") idx = (idx + 3) % 4;
    return directions[idx];
}

function moveForward(x, y, dir) {
    if (dir === "N") return [x - 1, y];
    if (dir === "E") return [x, y + 1];
    if (dir === "S") return [x + 1, y];
    if (dir === "W") return [x, y - 1];
    return [x, y];
}

function updateStatus(status) {
    rover.status = status;
    document.getElementById("statusText").textContent = status;
}

function updateCommand(cmd) {
    document.getElementById("commandText").textContent = cmd || "N/A";
}

function updateCommandText(text) {
    document.getElementById("commandText").textContent = text;
}

function drawMap() {
    const mapContainer = document.getElementById("map");
    mapContainer.innerHTML = "";

    for (let i = 0; i < rover.grid.length; i++) {
        const row = document.createElement("div");
        row.className = "flex";

        for (let j = 0; j < rover.grid[0].length; j++) {
            const cell = document.createElement("div");
            cell.className = "w-10 h-10 border border-gray-400 flex items-center justify-center text-xl";

            const isRoverHere = rover.x === i && rover.y === j;
            const wasVisited = rover.visited.some(([vx, vy]) => vx === i && vy === j);

            if (rover.grid[i][j] > 0) {
                cell.textContent = "💣";
            } else if (wasVisited) {
                cell.textContent = "⭐";
            }

            // Always draw the rover arrow last
            if (isRoverHere) {
                cell.textContent = getArrow(rover.dir);
            }

            row.appendChild(cell);
        }

        mapContainer.appendChild(row);
    }
}


async function loadMap() {
    const res = await fetch("/map");
    const map = await res.json();
    rover.grid = map.grid;
    rover.x = 0;
    rover.y = 0;
    rover.dir = "S";
    rover.commandIndex = 0;
    rover.running = false;
    rover.pendingMine = false;
    rover.commands = await getRoverCommands();
    rover.visited = [[rover.x, rover.y]];  // Mark starting tile as visited

    updateStatus("Not Started");
    updateCommand("N/A");
    drawMap();

}

async function getRoverCommands() {
    const roverId = new URLSearchParams(window.location.search).get("id");
    const res = await fetch("/rovers");
    const rovers = await res.json();
    const match = rovers.find(r => r.id == roverId);
    return match ? match.moves.split("") : [];
}

function step() {
    if (!rover.running || rover.commandIndex >= rover.commands.length) {
        updateStatus("Finished");
        updateCommandText("Done.");
        hideSpinner();
        rover.running = false;
        return;
    }

    const cmd = rover.commands[rover.commandIndex++];
    updateStatus("Moving");

    switch (cmd) {
        case "L":
            updateCommandText("Turning Left");
            rover.dir = rotate(rover.dir, "L");
            break;

        case "R":
            updateCommandText("Turning Right");
            rover.dir = rotate(rover.dir, "R");
            break;

        case "M":
            updateCommandText("Moving");
            const [nx, ny] = moveForward(rover.x, rover.y, rover.dir);

            if (nx < 0 || ny < 0 || nx >= rover.grid.length || ny >= rover.grid[0].length) {
                updateCommandText("Ignored: Out of Bounds");
                console.log(`↩️ Ignored move to (${nx}, ${ny}) — out of bounds`);
                drawMap();
                setTimeout(step, 500);
                return;
            }

            // Move the rover
            rover.x = nx;
            rover.y = ny;

            // Track visited spot
            rover.visited.push([rover.x, rover.y]);

            drawMap(); // Redraw map before checking mine logic

            if (rover.grid[nx][ny] > 0) {
                const nextCmd = rover.commands[rover.commandIndex];

                if (nextCmd === "D") {
                    rover.commandIndex++; // Consume D
                    updateCommandText("Disarming Mine...");
                    showSpinner();
                    console.log(`🧨 Received 'D' after stepping on mine at (${rover.x}, ${rover.y})`);

                    fetch("/dig", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({x: rover.x, y: rover.y}),
                    })
                        .then(res => res.json())
                        .then(data => {
                            hideSpinner();
                            if (data.success) {
                                rover.grid[rover.x][rover.y] = 0;
                                updateCommandText(`✅ PIN Found: ${data.pin} — Mine Disarmed`);
                                console.log(`✅ Mine at (${rover.x}, ${rover.y}) disarmed with PIN: ${data.pin}`);
                                drawMap();
                                setTimeout(step, 500);
                            } else {
                                updateStatus("Eliminated");
                                updateCommandText("❌ Dig failed.");
                                console.log(`❌ Failed to disarm mine at (${rover.x}, ${rover.y})`);
                                rover.running = false;
                                drawMap();
                            }
                        });
                    return;
                } else {
                    updateStatus("Eliminated");
                    updateCommandText("💥 No dig after stepping on mine.");
                    console.log(`💥 Eliminated! No dig after stepping on mine at (${rover.x}, ${rover.y})`);
                    hideSpinner();
                    rover.running = false;
                    drawMap();
                    return;
                }
            }

            break;

        case "D":
            updateCommandText("Dig ignored — not on a mine");
            console.log("❌ 'D' used but not on a mine — ignored");
            break;

        default:
            updateCommandText(`Unknown command: ${cmd}`);
            console.log(`❓ Unknown command: ${cmd}`);
    }

    drawMap();

    if (rover.running) {
        setTimeout(step, 500);
    }
}


document.getElementById("playButton").onclick = () => {
    if (rover.running) return;
    rover.running = true;
    step();
};

document.getElementById("pauseButton").onclick = () => {
    rover.running = false;
    updateStatus("Paused");
};

const params = new URLSearchParams(window.location.search);
const roverId = params.get("id");
if (roverId) {
    document.getElementById("dispatch-title").textContent = `Dispatching Rover "${roverId}"`;
}

loadMap();