import os
import serial
midi = serial.Serial('/dev/ttyAMA0', baudrate=38400,timeout=.001)

def cm():
    message = [0, 0, 0]
    i = 0
    while i < 3:
        data = midi.read(1)
        if len(data) == 0:
            return
        data = ord(data) # read a byte
        if data >> 7 != 0:  
          i = 0      # status byte!   this is the beginning of a midi message!
        message[i] = data
        i += 1
        if i == 2 and message[0] >> 4 == 12:  # program change: don't wait for a
          message[2] = 0                      # third byte: it has only 2 bytes
          i = 3
    
    messagetype = message[0] >> 4
    messagechannel = (message[0] & 15) + 1
    note = message[1] if len(message) > 1 else None
    velocity = message[2] if len(message) > 2 else None
    
    if messagechannel == 16:
        if messagetype == 9:    # Note on
            pkt = ['midi',' 1 ',str(note) + ' ' ,str(velocity)]
            pkt = ''.join(pkt)
            return pkt
        elif messagetype == 8:  # Note off
            pkt = ['midi',' 0']
            pkt = ''.join(pkt)
            return pkt
        else:
            return None
    
def check_midi():
    while True:
        pkt = cm()
        if pkt != None:
            os.system("echo '" + pkt + ";" + "' | pdsend 5000")