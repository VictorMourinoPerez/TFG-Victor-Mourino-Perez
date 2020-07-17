# !/usr/bin/env python
import socket
import datetime
import time
import os


def restart_connection(s):
    while True:
        time.sleep(5)
        try:
            s.close()
        except:
            pass
        time.sleep(5)
        try:
            s = socket.socket()
            s.settimeout(3)
            s.connect((TCP_IP, TCP_PORT))
            restart_data = s.recv(BUFFER_SIZE)
            if restart_data == '':
                raise socket.error
            else:
                write_log(1)
                break
        except:
            write_log(5)
            time.sleep(30)
    return s, restart_data


def write_log(arg):
    fileout = open(PATH + 'log.log', 'a')
    current_time = datetime.datetime.utcnow().strftime('%Y_%m_%d__%H_%M_%S')
    if arg == 0:
        fileout.write(current_time + '\t' + 'Script started successfully on ' + HOST + '.\n')
    elif arg == 1:
        fileout.write(
            current_time + '\t' + 'Script connected successfully with Radarcape on ' + TCP_IP + ' using port ' + str(
                TCP_PORT) + '\n')
    elif arg == 2:
        fileout.write(current_time + '\t' + 'New output file created successfully' + '\n')
    elif arg == 3:
        fileout.write(current_time + '\t' + 'Appending data into file ' + str(matching[0]) + '\n')
    elif arg == 4:
        fileout.write(current_time + '\t' + 'A connection error occurred. Trying to restart the connection.' + '\n')
    elif arg == 5:
        fileout.write(current_time +
                      '\t' + 'A connection error occurred again. Trying to restart the connection in 30 seconds.' + '\n')
    else:
        pass
    fileout.close()


TCP_IP = '10.4.118.83'
TCP_PORT = 10003
BUFFER_SIZE = 1024
MAX_SIZE = 100000
HOST= 'Raspberry'
#PATH = '/tmp/'
#PATH = 'C:/Users/marka/Desktop/'
PATH = 'D:\Documentos\TFG\Back-up torre\DATA-raspberry'
write_log(0)

s = socket.socket()
s.settimeout(3)
try:
    s.connect((TCP_IP, TCP_PORT))
except:
    write_log(4)
    s, data = restart_connection(s)
write_log(1)

available_files = os.listdir(PATH)

while True:
    filename = datetime.datetime.utcnow().strftime('%Y_%m_%d__%H_%M_%S')
    day = datetime.datetime.utcnow().strftime('%Y_%m_%d')
    start_datetime = datetime.datetime.utcnow()
    if any(day in element for element in available_files):
        matching = [elements for elements in available_files if day in elements]
        f = open(PATH + str(matching[0]), 'ab')
        write_log(3)
    else:
        f = open(PATH + str(filename) + '.dat', 'wb')
        write_log(2)
    current_datetime = datetime.datetime.utcnow()

    while start_datetime.day == current_datetime.day:
        current_datetime = datetime.datetime.utcnow()
        try:
            data = s.recv(BUFFER_SIZE)
            if data == '':
                raise socket.error
        except:  # Could be socket.error or socket.timeout
            write_log(4)
            s, data = restart_connection(s)
        f.write(data)
    f.close()
