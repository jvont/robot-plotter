import os
import random
import re
import serial
import time


# Input Parameters ------------------ -----------------------------------------

# arduino port
port_name = 'COM7'

# gcode folder
gcode_path = 'gcode/'

# motion detection timeout, in minutes
# 
# the last print will finish before this is checked
motion_timeout = 0.1 # 30

# paper feed amount (z-axis)
feed_rate = 100
feed_amount = 600

# ----------------------------------------------------------------------------


class termcols:
    """Terminal colours enum (see: https://stackoverflow.com/a/287944)"""

    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    ULINE = '\033[4m'
    END = '\033[0m'


def send_command(s: serial.Serial, cmd: str, log=False):
    """Send a command to GRBL, and wait for a response."""

    # send request
    req = cmd.strip()
    s.write((req + '\n').encode('ascii'))

    # collect response lines
    resp = s.readline().decode('ascii').strip()
    while s.in_waiting:
        resp += '\n' + s.readline().decode('ascii').strip()

    # log command status
    if log or resp != 'ok':
        col_resp = termcols.GREEN if resp == 'ok' else termcols.YELLOW
        print(f'{termcols.BLUE}{req} -> {col_resp}{resp}{termcols.END}')
    
    return resp


def get_status(s: serial.Serial):
    """Get current GRBL status (?)."""

    # send status request
    s.write('?\n'.encode('ascii'))

    # collect response lines
    resp = s.readline().decode('ascii').strip()
    while s.in_waiting:
        resp += '\n' + s.readline().decode('ascii').strip()

    return re.search(r'.*<([A-Z][a-z]+),.+>', resp).group(1)


def wake_grbl(s: serial.Serial):
    """Wake up GRBL, flush startup message."""

    s.write(b'\r\n\r\n')
    time.sleep(2)
    s.reset_input_buffer()


if __name__ == '__main__':
    # read gcode files, shuffle 'em up
    files = [os.path.join(gcode_path, f) for f in os.listdir(gcode_path)]
    random.shuffle(files)
    print(f'{termcols.MAGENTA}Shuffled GCode files:{termcols.CYAN}')
    for f in files:
        print(f)
    input(f'{termcols.END}Press [enter] if this is OK')

    # FIXME
    files = ['gcode/test.gcode']

    try:
        # open serial port and rouse the GRBL
        s = serial.Serial(port_name, 115200)
        wake_grbl(s)

        # send GRBL config commands
        print(f'{termcols.MAGENTA}Configuring GRBL{termcols.END}')
        with open('GRBL Config', 'r') as f:
            for line in f:
                send_command(s, line, log=True)

        # unlock GRBL
        send_command(s, '$X', log=True)

        # ~~~ main loop ~~~
        i = 0
        t0 = -60 * motion_timeout

        while 1:
            # run homing cycle and set origin
            print(f'{termcols.MAGENTA}Running homing cycle{termcols.END}')
            send_command(s, 'M3S60', log=True)
            send_command(s, '$H', log=True)
            send_command(s, 'G92X0Y0', log=True)

            # no movement detected within timeout
            if (time.time() - t0) > (60 * motion_timeout):
                print(f'{termcols.MAGENTA}Waiting for motion{termcols.END}')
                
                # send feed hold and wait for motion (resume pin)
                send_command(s, '!', log=True)
                while get_status(s) != 'Idle':
                    print(get_status(s))
                    time.sleep(0.3)
                    pass
                
                # reset start time
                t0 = time.time()

            # feed paper
            print(f'{termcols.MAGENTA}Feeding paper{termcols.END}')
            send_command(s, f'F{feed_rate}')
            send_command(s, f'G1Z{feed_amount}')
            
            # start printing
            print(f'{termcols.MAGENTA}Printing {files[i]}{termcols.END}')
            with open(files[i], 'r') as f:
                for line in f:
                    try:
                        send_command(s, line, log=True)
                    except KeyboardInterrupt:
                        # finish print early
                        send_command(s, '!', log=True)
                        break
            
            # move to next file
            i = (i + 1) % len(files)

            # FIXME
            input('file printed. press enter to contunie')

    finally:
        # close serial port
        s.close()
        print(f'{termcols.MAGENTA}Closed serial port.{termcols.END}')
