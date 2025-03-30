// rover-dashboard.js

let editingIndex = null;

async function loadMap() {
    const res = await fetch("/map");
    const map = await res.json();

    document.getElementById("height").value = map.height;
    document.getElementById("width").value = map.width;

    const container = document.getElementById("map");
    container.style.gridTemplateColumns = `repeat(${map.width}, 2.5rem)`;
    container.innerHTML = "";

    for (let i = 0; i < map.height; i++) {
        for (let j = 0; j < map.width; j++) {
            const cell = document.createElement("div");
            cell.className = "w-10 h-10 rounded-md border flex items-center justify-center text-xl cursor-pointer transition";

            if (map.grid[i][j] > 0) {
                cell.classList.add("bg-red-500", "text-white");
                cell.textContent = "💣";
            } else {
                cell.classList.add("bg-white", "hover:bg-blue-50");
            }

            cell.onclick = async () => {
                await fetch("/map/toggle-mine", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({x: i, y: j}),
                });
                loadMap();
            };

            container.appendChild(cell);
        }
    }
}

async function loadRovers() {
    const res = await fetch("/rovers");
    const rovers = await res.json();
    const tableBody = document.getElementById("roverTableBody");
    tableBody.innerHTML = "";

    rovers.forEach((rover, index) => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td class="px-4 py-2 border-b border-r text-sm text-gray-800">${rover.id}</td>
            <td class="px-4 py-2 border-b text-sm text-gray-700 break-words">${rover.moves}</td>
            <td class="px-4 py-2 border-b text-sm">
                <button onclick="openModal(${index}, '${rover.id}', '${rover.moves}')" class="bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600">Edit</button>
                <button onclick="deleteRover(${index})" class="bg-red-500 text-white px-3 py-1 rounded ml-2 hover:bg-red-600">Delete</button>
                <button onclick="dispatchRover('${rover.id}')" class="bg-yellow-500 text-white px-3 py-1 rounded ml-2 hover:bg-yellow-600">Dispatch</button>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

function dispatchRover(roverId) {
    window.open(`/static/dispatch.html?id=${encodeURIComponent(roverId)}`, "_blank");
}

function openModal(index, id, moves) {
    editingIndex = index;
    document.getElementById("editRoverId").value = id;
    document.getElementById("editRoverMoves").value = moves;
    document.getElementById("editModal").classList.remove("hidden");
}

function closeModal() {
    editingIndex = null;
    document.getElementById("editModal").classList.add("hidden");
}

document.getElementById("editForm").onsubmit = async function (e) {
    e.preventDefault();
    const id = document.getElementById("editRoverId").value;
    const moves = document.getElementById("editRoverMoves").value;

    if (!/^([RMLD]*)$/.test(moves)) {
        alert("❌ Invalid command. Only R, L, M, D are allowed.");
        return;
    }

    const res = await fetch("/rovers/update", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({index: editingIndex, id, moves})
    });

    const result = await res.json();
    if (result.status === "success") {
        closeModal();
        loadRovers();
    } else {
        alert("❌ Failed to update rover: " + result.message);
    }
};

document.getElementById("createForm").onsubmit = async function (e) {
    e.preventDefault();

    const id = document.getElementById("createRoverId").value.trim();
    const moves = document.getElementById("createRoverMoves").value.trim();

    if (!/^([RMLD]*)$/i.test(moves)) {
        alert("❌ Invalid command. Only R, L, M, D are allowed.");
        return;
    }

    const res = await fetch("/rovers");
    const rovers = await res.json();
    if (rovers.some(rover => rover.id === id)) {
        alert("❌ Rover ID must be unique.");
        return;
    }

    const saveRes = await fetch("/rovers/create", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({id, moves})
    });

    const result = await saveRes.json();
    if (result.status === "success") {
        alert("✅ Rover created!");
        closeCreateModal();
        loadRovers();
    } else {
        alert("❌ Failed to create rover: " + result.message);
    }
};

function openCreateModal() {
    document.getElementById("createRoverId").value = "";
    document.getElementById("createRoverMoves").value = "";
    document.getElementById("createModal").classList.remove("hidden");
}

function closeCreateModal() {
    document.getElementById("createModal").classList.add("hidden");
}

async function deleteRover(index) {
    if (!confirm("Are you sure you want to delete this rover?")) return;

    const res = await fetch(`/rovers/${index}`, {method: "DELETE"});
    const result = await res.json();

    if (result.status === "success") {
        loadRovers();
    } else {
        alert("Failed to delete rover: " + result.message);
    }
}

document.getElementById("mapForm").onsubmit = async function (e) {
    e.preventDefault();  // Prevent page reload

    const height = parseInt(document.getElementById("height").value);
    const width = parseInt(document.getElementById("width").value);

    if (isNaN(height) || isNaN(width) || height <= 0 || width <= 0) {
        alert("Invalid dimensions.");
        return;
    }

    const res = await fetch("/map", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ height, width })
    });

    const result = await res.json();
    if (result.status === "success") {
        await loadMap(); // Refresh the visual grid
    } else {
        alert("❌ Failed to update map size.");
    }
};


async function updateMapSizeDynamically() {
    const height = parseInt(document.getElementById("height").value);
    const width = parseInt(document.getElementById("width").value);

    if (isNaN(height) || isNaN(width) || height <= 0 || width <= 0) return;

    const res = await fetch("/map", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ height, width })
    });

    const result = await res.json();
    if (result.status === "success") {
        await loadMap();
    } else {
        console.error("Map size update failed");
    }
}

document.getElementById("height").addEventListener("input", updateMapSizeDynamically);
document.getElementById("width").addEventListener("input", updateMapSizeDynamically);


// Initial loading
loadMap();
loadRovers();
