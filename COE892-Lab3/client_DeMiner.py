'''
De-Miner Client
'''

import pika
import hashlib
import random
import time

# Function to publish defused mine PIN to Defused-Mines queue
def publish_to_defused_mines(pin_info):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='Defused-Mines')

        channel.basic_publish(exchange='',
                              routing_key='Defused-Mines',
                              body=pin_info)
        print(f"[Defused-Mines] Published: {pin_info}")
        connection.close()
    except Exception as e:
        print(f"RabbitMQ Publish Error: {str(e)}")

# Function to process and disarm a mine
def disarm_mine(mine_info, deminer_number):
    print(f"Deminer {deminer_number} is disarming the mine: {mine_info}")
    # Generate a random PIN for the mine
    rand = random.randint(100, 999)
    tempKey = str(rand) + mine_info
    hashKey = hashlib.sha256(tempKey.encode()).hexdigest()

    # Ensure the PIN starts with '0'
    while hashKey[0] != '0':
        print("Invalid PIN detected, retrying...")
        rand = random.randint(100, 999)
        tempKey = str(rand) + mine_info
        hashKey = hashlib.sha256(tempKey.encode()).hexdigest()

    print("Valid PIN detected, mine defused.")
    pin_info = f"Deminer {deminer_number}, Mine: {mine_info}, PIN: {hashKey}"

    # Publish the defused PIN to Defused-Mines
    publish_to_defused_mines(pin_info)

# Function to subscribe to Demine-Queue and process mines
def subscribe_to_demine_queue(deminer_number):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='Demine-Queue')

    def callback(ch, method, properties, body):
        mine_info = body.decode()
        print(f"[Demine-Queue] Received: {mine_info}")

        # Disarm the mine if available
        disarm_mine(mine_info, deminer_number)
        time.sleep(2)  # Simulate time taken to disarm

    channel.basic_consume(queue='Demine-Queue', on_message_callback=callback, auto_ack=True)
    print(f"Deminer {deminer_number} is waiting for tasks...")
    channel.start_consuming()

# Main function to handle user input and start the deminer
def main():
    deminer_number = input("Enter the deminer number (1 or 2): ")
    if deminer_number not in ['1', '2']:
        print("Invalid deminer number! Use 1 or 2.")
        return

    subscribe_to_demine_queue(deminer_number)

if __name__ == "__main__":
    main()
