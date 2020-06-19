import serial
import datetime
import time
import os.path
import json
import re
import sys
import logging

logger = logging.getLogger('cyckei')

EOL = b'\r\n'
weight_conversion = {'g':1, 'mg':0.001, 'kg':1000., 'oz':0.0352739619, 'lb':0.00220462262}

class DataController(object):
    def __init__(self):
        self.name = "mettler-scale"
        logger.info("Initializing Mettler Toledo Scale Plugin...")

        self.scale = MettlerLogger(PORT="COM5")
        self.model = scale.get_balance_model()
        self.serial = scale.get_balance_serial()
        logger.info(f"Model: {self.model}, Serial: {self.serial}")

    def read(self):
        logger.debug("Reading Weight from Scale...")
        self.weight = scale.get_weight()
        return self.weight

class MettlerLogger(object):
    def __init__(self,
        ACCEPTABLE_STATUS=['S','SD'],
        TIMEFORMAT='%Y-%m-%d %H:%M:%S.%f',
        PORT=None,
        BAUDRATE=9600,
        BYTESIZE=serial.EIGHTBITS,
        PARITY=serial.PARITY_NONE,
        XONXOFF=True,
        NAME=None,
        maxi=100000000000,
        verbosity=1,
        DRY_WEIGHT=None,
        DENSITY=0.963):

        timestamp_start = time.time()
        date_start = datetime.datetime.fromtimestamp(timestamp_start)
        date_start_str = date_start.strftime(TIMEFORMAT)

        self.options = {
            'description':'Logfile of data collected from a MettlerToledo balance. Header is JSON, data is CSV',
            'serial':{
                'port':PORT,
                'baudrate':BAUDRATE,
                'bytesize':BYTESIZE,
                'parity':PARITY,
                'xonxoff':XONXOFF},
            'date_start':date_start_str,
            'time_format':TIMEFORMAT,
            'timestamp':timestamp_start,
            'dry_weight':DRY_WEIGHT,
            'density':DENSITY,
            'data_columns':[
                {'index':0,
                 'name':'time',
                 'unit':'seconds',
                 'description':'time elapsed in seconds since date_start'},
                {'index':1,
                 'name':'weight',
                 'unit':'grams',
                 'description':'instantaneous weight measured by Mettler-Toledo Balance in grams'},
                {'index':2,
                 'name':'status',
                 'unit':' text',
                 'description':'State returned by balance "S" means a stable state, "SI" means a transient state'}],

            'name':NAME,
            'verbosity':verbosity,
            'balance':{
                'model':None,
                'serial':None}
            }

    def communicate(self, command):
        '''
        open a connection, send command, read output, then close.
        return result. Returns Non on failure
        '''
        ser = serial.Serial(port=str(self.options['serial']['port']),
                            baudrate=self.options['serial']['baudrate'],
                            bytesize=self.options['serial']['bytesize'],
                            parity=self.options['serial']['parity'],
                            xonxoff=self.options['serial']['xonxoff'],
                            timeout=10)

        command = command.encode('utf-8')
        ser.write(command + EOL)
        s = ser.readline().decode('utf-8')
        ser.close()
        return s

    def get_balance_model(self):
        try:
            t = self.communicate("I2")
            return re.search(r'"(.+)"',t).groups()[0]
        except:
            return None

    def get_balance_serial(self):
        try:
            t = self.communicate("I4")
            return re.search(r'"(.+)"',t).groups()[0]
        except:
            return None

    def get_weight(self, command="SI"):
        '''
        Opens a connection with balance.
        Requests weight using command.
        Parses the balance's response.
        Closes connection.
        Returns the weight in grams.

        Parameters:
            command:
                command string to send to balance, defaults to SI, the immediate
                unequilibrated weight. End line characters should not be included

        Returns:
            weight:
                weight in grams or None on failure
        '''

        weight = None
        weight_d = {'Status':None, 'WeightValue':None, 'Unit':None}
        try:
            #get a weight and close the connection
            s = self.communicate(command)

            if len(s.split()) == 4 or len(s.split()) == 3:
                pars = s.split()
                weight_d = {'Status':pars[0], 'WeightValue':float(pars[-2]), 'Unit':pars[-1]}
                weight = weight_d['WeightValue'] * weight_conversion[weight_d['Unit']]

        except (serial.SerialException) as e:
            if self.options['verbosity'] > 0:
                print('Failed with error: %s' %e)

        return weight, weight_d
