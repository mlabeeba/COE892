import grpc
import sys
import rover_service_pb2
import rover_service_pb2_grpc

def get_map(stub):
    response = stub.GetMap(rover_service_pb2.Empty())
    return response.map

def get_commands(stub, rover_id):
    response = stub.GetCommands(rover_service_pb2.CommandsRequest(rover_id=rover_id))
    return response.commands

def report_status(stub, success):
    response = stub.ReportExecutionStatus(rover_service_pb2.ExecutionStatusRequest(success=success))
    print("Status reported:", response.acknowledged)

def main(rover_id):
    # Connect to the gRPC server
    channel = grpc.insecure_channel('localhost:50051')
    stub = rover_service_pb2_grpc.RoverServiceStub(channel)

    # Retrieve the map
    map_data = get_map(stub)
    print("Map Data:", map_data)

    # Retrieve commands
    commands = get_commands(stub, rover_id)
    print("Commands for Rover", rover_id, ":", commands)

    # Execute commands (simplified)
    for command in commands:
        print("Executing command:", command)
        # Add logic to handle different command types and interactions with the server

    # Example of reporting the execution status
    report_status(stub, True)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python rover_client.py [rover_id]")
        sys.exit(1)
    rover_id = int(sys.argv[1])
    main(rover_id)
