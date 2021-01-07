import serial

if __name__ == "__main__":

    with serial.Serial(port = "COM11", baudrate=115200,
                            bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE) as serialPort:
        while(1):
            if serialPort.in_waiting > 0:
                # Read data out of the buffer until a carraige return / new line is found
                serialString = serialPort.readline()

                # Print the contents of the serial data
                print(serialString.decode('Ascii'))

                # Tell the device connected over the serial port that we recevied the data!
                # The b at the beginning is used to indicate bytes!
                serialPort.write(40)