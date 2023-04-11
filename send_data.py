import serial
import time


# Input Parameters ------------------ -----------------------------------------

port_name = 'COM4'
# gcode_path = 'gcode/stump4plotter.gcode'
gcode_path = 'gcode/Stumpoutlineandrings2.gcode'

# ----------------------------------------------------------------------------


def sendCommand(cmd: str, log=False):
    """Send a command to GRBL, and wait for a response."""
    req = cmd.strip()
    s.write((req + '\n').encode('ascii'))
    res = s.readline().decode('ascii').strip()
    if log or res != 'ok':
        print(f'[COMMAND] {req} -> {res}')


if __name__ == '__main__':
    # open serial port
    s = serial.Serial(port_name, 115200)

    # wake up GRBL
    s.write(b'\r\n\r\n')
    time.sleep(2)
    s.flushInput()

    # send config
    with open('GRBL Config', 'r') as f:
        for line in f:
            sendCommand(line)

    print('Configuration Complete.')

    # unlock/calibrate
    sendCommand('$X', log=True)
    sendCommand('M3S60', log=True)
    sendCommand('$H', log=True)
    sendCommand('G92X0Y0', log=True)

    # send gcode commands
    input(f'Press <Enter> to run \'{gcode_path}\'.')

    with open(gcode_path, 'r') as f:
        for line in f:
            try:
                sendCommand(line, log=True)
            except KeyboardInterrupt:
                sendCommand('!', log=True)
                break
        
    # phone home
    sendCommand('M3S60', log=True)
    sendCommand('$H', log=True)

    # close serial port
    s.close()
