'''
Ground Control Server
'''

from concurrent import futures
import logging
import grpc
import requests
import pika
import buffer_pb2
import buffer_pb2_grpc
import threading


class gRPC_Server(buffer_pb2_grpc.GroundControlServicer):
    # method to fetch and return the map from a text file
    def getMap(self, request, context):
        mapFile = open('map1.txt', 'r')
        global rows
        global columns
        mapDirections = mapFile.readline().split()
        mapRows = mapDirections[0]
        mapColumns = mapDirections[1]

        print("\nrows " + mapRows + "  columns " + mapColumns)
        print("Rover Starts Facing South at (0, 0)")
        print("[ 0 = no mine, 1 = mine ]\n")

        print("Map:")
        mapConents = ""
        for line in mapFile:
            mapConents += line

        print(mapConents)
        return buffer_pb2.mapReply(map=str(mapConents), rows=mapRows, column=mapColumns)

    # method to fetch and return commands for the rover from an external API
    def getCommands(self, request, context):
        apiResponse = requests.get('https://coe892.reev.dev/lab1/rover/' + str(request.roverNum))
        apiContent = apiResponse.json()
        move = apiContent['data']['moves']

        print("Commands: " + move)
        return buffer_pb2.commandReply(moves=move)

    # method to fetch and return the serial number of a mine based on the rover's position
    def getMineSerialNumber(self, request, context):
        with open('mines.txt', 'r') as minesFile:
            mineData = minesFile.readlines()
        roverPosition = list(map(int, request.roverPos.split(" ")))
        if roverPosition[1] < len(mineData):
            serial_num = mineData[roverPosition[1]].strip()
            return buffer_pb2.mineSerialNumberReply(serialNum=serial_num)
        else:
            return buffer_pb2.mineSerialNumberReply(serialNum="Invalid Position")

    # method to receive and acknowledge a mine pin
    def getMinePin(self, request, context):
        pin = request
        print(pin)
        return buffer_pb2.minePinReply(pin="Pin received")

    # acknowledge a successful operation
    def getSuccess(self, request, context):
        print(request.status)
        return buffer_pb2.successReply(response="Success")


# --------- RabbitMQ Subscriber for Defused-Mines ---------
def rabbitmq_listener():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='Defused-Mines')

        def callback(ch, method, properties, body):
            print(f"[Defused-Mines] Received: {body.decode()}")
            # Log to a file
            with open("defused_mines.log", "a") as log_file:
                log_file.write(f"{body.decode()}\n")

        channel.basic_consume(queue='Defused-Mines', on_message_callback=callback, auto_ack=True)
        print("[Defused-Mines] Waiting for messages...")
        channel.start_consuming()
    except Exception as e:
        print(f"RabbitMQ Listener Error: {str(e)}")


# function to configure and start the gRPC server
def serve():
    # Create a gRPC server to handle requests
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    buffer_pb2_grpc.add_GroundControlServicer_to_server(gRPC_Server(), server)

    # Specify the port for the server to listen on
    port = 1500
    server.add_insecure_port('[::]:{}'.format(port))

    # Start the server
    server.start()
    print("gRPC Server started. Listening on port {}".format(port))

    # Start RabbitMQ listener in a separate thread
    rabbitmq_thread = threading.Thread(target=rabbitmq_listener, daemon=True)
    rabbitmq_thread.start()

    # Run the gRPC server
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Server stopping...")
        server.stop(0)
        print("Server stopped successfully.")


if __name__ == '__main__':
    logging.basicConfig()
    serve()
