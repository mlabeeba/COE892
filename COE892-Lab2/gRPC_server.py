import grpc
from concurrent import futures
import rover_service_pb2
import rover_service_pb2_grpc

# Load the map from the file
def load_map():
    with open("files/map1.txt", "r") as file:
        return [line.strip() for line in file.readlines()]

# Load mine serial numbers
def load_mine_serials():
    with open("files/mines.txt", "r") as file:
        return [line.strip() for line in file.readlines()]

# Assuming the rover_paths directory contains files named path_1.txt, path_2.txt, ..., path_10.txt
def load_rover_commands(rover_id):
    try:
        with open(f"files/rover_paths/path_{rover_id}.txt", "r") as file:
            return [line.strip().replace(' ', '') for line in file.readlines()]
    except FileNotFoundError:
        return []

class RoverService(rover_service_pb2_grpc.RoverServiceServicer):
    def GetMap(self, request, context):
        map_data = load_map()
        return rover_service_pb2.MapResponse(map=map_data)

    def GetCommands(self, request, context):
        commands = load_rover_commands(request.rover_id)
        return rover_service_pb2.CommandsResponse(commands=commands)

    def GetMineSerial(self, request, context):
        serials = load_mine_serials()
        # Example: Return the first serial number, adjust based on logic needed
        return rover_service_pb2.MineSerialResponse(serialNumber=serials[0])

    def ReportExecutionStatus(self, request, context):
        # Implement based on your requirements
        return rover_service_pb2.ExecutionStatusResponse(acknowledged=True)

    def ShareMinePIN(self, request, context):
        # Implement based on your requirements
        return rover_service_pb2.PINResponse(accepted=True)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rover_service_pb2_grpc.add_RoverServiceServicer_to_server(RoverService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
