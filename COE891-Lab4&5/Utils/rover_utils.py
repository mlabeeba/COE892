from pydantic import BaseModel

ROVER_FOLDER = "rover_info"

# ------------------------
# DATA MODELS
# ------------------------
class NewRover(BaseModel):
    id: str
    moves: str

class RoverUpdate(BaseModel):
    index: int
    id: str
    moves: str