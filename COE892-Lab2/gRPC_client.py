import hashlib
import logging
import random

# import the protobuf files for gRPC service and message definitions
import grpc
import buffer_pb2
import buffer_pb2_grpc

# function to control the rover's operations
def run():
    # start connection with the gRPC server
    with grpc.insecure_channel('localhost:1500') as channel:
        stub = buffer_pb2_grpc.GroundControlStub(channel)
        response = stub.getMap(buffer_pb2.mapRequest())
    print("Successfully Connected to Server!\n")

    # global variables to track rover's state
    global roverDirection
    global startingPosition
    global roverHealth
    global routeArray
    global rows
    global columns
    global moves
    global currentMoves

    # extracting the map data from the server's response
    array = response.map
    rows = response.rows
    columns = response.column

    print("Map: ")
    print(array)
    print("Rows: " + rows + ", " + "Columns: " + columns + "\n")

    # start another connection to get rover's commands
    with grpc.insecure_channel('localhost:1500') as channel:
        stub = buffer_pb2_grpc.GroundControlStub(channel)
        global roverNumber
        roverNumber = input("Input the rover number: ")

        response2 = stub.getCommands(buffer_pb2.commandRequest(roverNum=str(roverNumber)))
        print(str(response2))
    # Initialize rover's starting state
    roverDirection = "South"
    startingPosition = [0, 0]
    roverHealth = 'Alive'

    f = open("path_" + str(roverNumber) + ".txt", "w+")
    # process the received map into a 2D array
    text = array.strip().split("\n")
    routeArray = [list(map(int, line.split())) for line in text]
    # starting position
    routeArray[0][0] = "*"
    moves = response2.moves

    # process & execute received commands
    for j in range(len(moves)):
        # check current command needs to move forward and if so execute the forward movement function
        if moves[j] == 'M':
            forward()
        # check if command is to move right, and adjust the rover's direction
        elif moves[j] == 'R':
            roverDirection = right(roverDirection)
        # check if command is to move left, and adjust the rover's direction
        elif moves[j] == 'L':
            roverDirection = left(roverDirection)
        # check if the command is to dig at the current position
        elif moves[j] == 'D':
            try:
                # If the current position has a mine ('1'), start the digging process
                if 0 <= startingPosition[1] < len(routeArray) and 0 <= startingPosition[0] < len(routeArray[startingPosition[1]]):
                    if routeArray[startingPosition[1]][startingPosition[0]] == 1:
                        print("Start Digging")

                        # start a gRPC connection to get the mine's serial number
                        with grpc.insecure_channel('localhost:1500') as channel:
                            stub = buffer_pb2_grpc.GroundControlStub(channel)
                            response3 = stub.getMineSerialNumber(buffer_pb2.mineSerialNumberRequest(
                                roverPos=(str(startingPosition[0]) + " " + str(startingPosition[1]))))

                        print(response3)
                        # disarm the mine by generating a hash key and checking if it's valid
                        rand = random.randint(100, 999)
                        tempKey = str(rand) + str(routeArray[startingPosition[1]][startingPosition[0]])
                        print("Temporary key = ", tempKey)
                        hashKey = hashlib.sha256(tempKey.encode()).hexdigest()
                        print("Hash key = " + hashKey)
                        while hashKey[0] != '0':
                            print("Invalid PIN Detected, Attempting to Retry with a Different PIN")
                            rand = random.randint(100, 999)
                            tempKey = str(rand) + str(routeArray[startingPosition[1]][startingPosition[0]])
                            # print("Temporary key = " + tempKey)
                            hashKey = hashlib.sha256(tempKey.encode()).hexdigest()
                            print("Hash key = " + hashKey)
                        print("Valid Print Detected, Disarming Mine")

                        # send valid pin back to the server to disarm the mine
                        with grpc.insecure_channel('localhost:1500') as channel:
                            stub = buffer_pb2_grpc.GroundControlStub(channel)
                            response4 = stub.getMinePin(buffer_pb2.minePinRequest(mineNum=hashKey))
                    else:
                        print("Detecting Mine ... No mine")
                else:
                    print("Position: Out of map bounds")
            except IndexError:
                print("Error in Index")

            # print the rover's current direction, position, and health state after each command
            print("Direction: " + roverDirection)
            print("Current Position: ", startingPosition)
            print("Current State: " + roverHealth)
            print("Movement Completed\n\n")
        # if rover encounters a mine without a dig command, it is destroyed
        elif routeArray[startingPosition[0]][startingPosition[1]] != '0':
            print("Mine Located! No Digging Attempt Made, Resulting in Explosion!")
            roverHealth = "Dead"
            break

    # saving the rover's path to a file after completing all commands
    for row in routeArray:
        f.write(" ".join(map(str, row)) + "\n")

    # report the rover's success or failure back to the server
    if roverHealth == "Alive":
        with grpc.insecure_channel('localhost:1500') as channel:
            stub = buffer_pb2_grpc.GroundControlStub(channel)
            response5 = stub.getSuccess(
                buffer_pb2.successReply(response="Rover " + str(roverNumber) + " has completed"))
    else:
        with grpc.insecure_channel('localhost:1500') as channel:
            stub = buffer_pb2_grpc.GroundControlStub(channel)
            response5 = stub.getSuccess(
                buffer_pb2.successReply(response="Rover " + str(roverNumber) + " has exploded"))

# move the rover forward based on its current direction and position
def forward():
    try:
        if roverDirection == 'North':
            if startingPosition[1] == 0:
                print("Position: Boundary Reached ... Command Ignored")
                return
            if routeArray[startingPosition[1] - 1][startingPosition[0]] == '1':
                print("Collision Detected ... Rover Destroyed")
                roverHealth = 'Dead'
                return roverHealth

            startingPosition[1] = startingPosition[1] - 1
            routeArray[startingPosition[1]][startingPosition[0]] = "*"

        elif roverDirection == 'South':
            if startingPosition[1] == rows:
                print("Position: Boundary Reached ... Command Ignored")
                return
            if routeArray[startingPosition[1] + 1][startingPosition[0]] == '1':
                print("Collision Detected ... Rover Destroyed")
                roverHealth = 'Dead'
                return roverHealth
            startingPosition[1] = startingPosition[1] + 1
            routeArray[startingPosition[1]][startingPosition[0]] = "*"

        elif roverDirection == 'East':
            if startingPosition[0] == columns:
                print("Position: Boundary Reached ... Command Ignored")
                return
            if routeArray[startingPosition[1]][startingPosition[0] + 1] == '1':
                print("Collision Detected ... Rover Destroyed")
                roverHealth = 'Dead'
                return roverHealth
            startingPosition[0] = startingPosition[0] + 1
            routeArray[startingPosition[1]][startingPosition[0]] = "*"

        elif roverDirection == 'West':
            if startingPosition[0] == 0:
                print("Position: Boundary Reached ... Command Ignored")
                return
            if routeArray[startingPosition[1]][startingPosition[0] - 1] == '1':
                print("Collision Detected ... Rover Destroyed")
                roverHealth = 'Dead'
                return roverHealth
            startingPosition[0] = startingPosition[0] - 1
            routeArray[startingPosition[1]][startingPosition[0]] = "*"
    except IndexError:
        print("Position: Out of map bounds")

# function to turn the rover left
def left(roverDirection):
    if roverDirection == 'North':
        roverDirection = 'West'
    elif roverDirection == 'East':
        roverDirection = 'North'
    elif roverDirection == 'South':
        roverDirection = 'East'
    elif roverDirection == 'West':
        roverDirection = 'South'
    return roverDirection

# function to turn the rover right
def right(roverDirection):
    if roverDirection == 'North':
        roverDirection = 'East'
    elif roverDirection == 'East':
        roverDirection = 'South'
    elif roverDirection == 'South':
        roverDirection = 'West'
    elif roverDirection == 'West':
        roverDirection = 'North'
    return roverDirection


if __name__ == '__main__':
    logging.basicConfig()
    run()
