import os
import random
import re
import serial
import time


# Input Parameters ------------------ -----------------------------------------

# arduino port
port_name = 'COM4'

# gcode folder
gcode_path = 'gcode/'

# timeout after which the printer will not start a new print, in minutes
print_stop_time = 0.1 # 30

# delay before starting a new print, in seconds
print_start_delay = 5

# paper feeder settings (GCode Z-Axis)
paper_feed_rate = 100
paper_feed_amount = 1 # 100

# set flag to perform a homing cycle after each print
homing_after_print = True

# set flag to bypass motion detector
bypass_feed_hold = False

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


def print_status(msg: str, col=termcols.MAGENTA):
    """Print a status message (colourized)."""
    
    print(f'{col}{msg}{termcols.END}')


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


def home_grbl(s: serial.Serial, log=True):
    """Perform a GRBL homing cycle."""

    send_command(s, 'M3S60', log=log)
    send_command(s, '$H', log=log)
    send_command(s, 'G92X0Y0', log=log)


if __name__ == '__main__':
    # read gcode files, shuffle 'em up
    files = [os.path.join(gcode_path, f) for f in os.listdir(gcode_path)]
    random.shuffle(files)
    print(f'{termcols.MAGENTA}Shuffled GCode files:{termcols.CYAN}')
    for f in files:
        print(f)

    # input(f'{termcols.END}Press [enter] if this is OK')

    # open serial port
    with serial.Serial(port_name, 115200) as s:
        # rouse the GRBL
        wake_grbl(s)

        # send GRBL config commands
        print_status('Configuring GRBL')
        with open('GRBL Config', 'r') as f:
            for line in f:
                send_command(s, line, log=True)

        # unlock GRBL, set absolute positioning
        send_command(s, '$X', log=True)
        send_command(s, f'G90', log=True)

        # run homing cycle and set origin
        print_status('Running homing cycle')
        home_grbl(s)

        # ~~~ main loop ~~~
        i = 0
        t0 = -60 * print_stop_time
        while 1:
            # no movement detected within timeout
            if (time.time() - t0) > (60 * print_stop_time):
                
                # send feed hold and wait for motion (resume pin)
                if not bypass_feed_hold:
                    print_status('Waiting for motion...')
                    send_command(s, '!', log=True)
                    print_status('Motion detected!')
                
                # reset start time
                t0 = time.time()

            # wait before starting paper feed
            time.sleep(print_start_delay)

            # feed paper relative to current position
            print_status('Feeding paper')
            send_command(s, f'G91', log=True)
            send_command(s, f'F{paper_feed_rate}', log=True)
            send_command(s, f'G1Z{paper_feed_amount}', log=True)
            send_command(s, f'G90', log=True)
            
            # start printing
            print_status(f'Printing {files[i]}')
            with open(files[i], 'r') as f:
                for line in f:
                    try:
                        send_command(s, line, log=True)
                    except KeyboardInterrupt:
                        # finish print early
                        send_command(s, '!', log=True)
                        break
            
            # wait until print is finished
            print_status(f'Finishing {files[i]}')
            while get_status(s) == 'Run':
                pass

            # rerun homing cycle
            if homing_after_print:
                print_status('Rerun homing cycle')
                home_grbl(s)

            # move to next file
            i = (i + 1) % len(files)

    print_status('Closed serial port.')
