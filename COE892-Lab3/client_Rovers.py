'''
Rover Client
'''

import logging
import grpc
import pika
import buffer_pb2
import buffer_pb2_grpc

# Publish mine details to Demine-Queue
def publish_to_demine_queue(mine_info):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='Demine-Queue')
        channel.basic_publish(exchange='',
                              routing_key='Demine-Queue',
                              body=mine_info)
        print(f"[Demine-Queue] Published: {mine_info}")
        connection.close()
    except Exception as e:
        print(f"RabbitMQ Publish Error: {str(e)}")

# function to control the rover's operations
def run():
    # start connection with the gRPC server
    with grpc.insecure_channel('localhost:1500') as channel:
        stub = buffer_pb2_grpc.GroundControlStub(channel)
        response = stub.getMap(buffer_pb2.mapRequest())
    print("Successfully Connected to Server!\n")

    global roverDirection, startingPosition, roverHealth, routeArray, rows, columns, moves, currentMoves

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


    #f = open("path_" + str(roverNumber) + ".txt", "w+")
    # process the received map into a 2D array
    text = array.strip().split("\n")
    routeArray = [list(map(int, line.split())) for line in text]
    # starting position
    routeArray[0][0] = "*"
    moves = response2.moves

    # process & execute received commands
    for j in range(len(moves)):
        if moves[j] == 'M':
            forward()
        elif moves[j] == 'R':
            roverDirection = right(roverDirection)
        elif moves[j] == 'L':
            roverDirection = left(roverDirection)

        # Check for mine at the current position
        try:
            if routeArray[startingPosition[1]][startingPosition[0]] == 1:
                print("Mine detected!")
                with grpc.insecure_channel('localhost:1500') as channel:
                    stub = buffer_pb2_grpc.GroundControlStub(channel)
                    response3 = stub.getMineSerialNumber(buffer_pb2.mineSerialNumberRequest(
                        roverPos=(str(startingPosition[0]) + " " + str(startingPosition[1]))))

                serial_number = response3.serialNum
                if serial_number != "Invalid Position":
                    mine_info = f"Rover: {roverNumber}, Position: ({startingPosition[0]}, {startingPosition[1]}),\
                    Serial: {serial_number}"
                    publish_to_demine_queue(mine_info)
            else:
                print("No mine detected.")
        except IndexError:
            print("Position: Out of map bounds")

        print("Direction: " + roverDirection)
        print("Current Position: ", startingPosition)
        print("Current State: " + roverHealth)
        print("Movement Completed\n\n")

    '''
    # saving the rover's path to a file after completing all commands
    for row in routeArray:
        f.write(" ".join(map(str, row)) + "\n")
    '''

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
        if roverDirection == 'South' and startingPosition[1] + 1 < int(rows):
            startingPosition[1] += 1
        elif roverDirection == 'North' and startingPosition[1] - 1 >= 0:
            startingPosition[1] -= 1
        elif roverDirection == 'East' and startingPosition[0] + 1 < int(columns):
            startingPosition[0] += 1
        elif roverDirection == 'West' and startingPosition[0] - 1 >= 0:
            startingPosition[0] -= 1
    except IndexError:
        print("Position: Out of map bounds")

# function to turn the rover left
def left(roverDirection):
    directions = ['North', 'West', 'South', 'East']
    return directions[(directions.index(roverDirection) + 1) % 4]

# function to turn the rover right
def right(roverDirection):
    directions = ['North', 'East', 'South', 'West']
    return directions[(directions.index(roverDirection) + 1) % 4]

if __name__ == '__main__':
    logging.basicConfig()
    run()
