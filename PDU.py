class AmpliferState:
    port = 'COM3'  # You will need to change this

    volt = 0
    is_pulsed = True
    start_flag = False
    def __init__(self, data):
        self.enabled = bool(data[0])
        self.phaseTracking = bool(data[1])
        self.currentTracking = bool(data[2])
        self.powerTracking = bool(data[3])
        self.errorAmp = bool(data[4])
        self.errorLoad = bool(data[5])
        self.errorTemperature = bool(data[6])
        self.voltage = float(unpack('f', data[8:12])[0])
        self.frequency = float(unpack('f', data[12:16])[0])
        self.minFrequency = float(unpack('f', data[16:20])[0])
        self.maxFrequency = float(unpack('f', data[20:24])[0])
        self.phaseSetpoint = float(unpack('f', data[24:28])[0])
        self.phaseControlGain = float(unpack('f', data[28:32])[0])
        self.currentSetpoint = float(unpack('f', data[32:36])[0])
        self.currentControlGain = float(unpack('f', data[36:40])[0])
        self.powerSetpoint = float(unpack('f', data[40:44])[0])
        self.powerControlGain = float(unpack('f', data[44:48])[0])
        self.maxLoadPower = float(unpack('f', data[48:52])[0])
        self.ampliferPower = float(unpack('f', data[52:56])[0])
        self.loadPower = float(unpack('f', data[56:60])[0])
        self.temperature = float(unpack('f', data[60:64])[0])
        self.measuredPhase = float(unpack('f', data[64:68])[0])
        self.measuredCurrent = float(unpack('f', data[68:72])[0])
        self.Impedance = float(unpack('f', data[72:76])[0])
        self.transformerTruns = float(unpack('f', data[76:80])[0])

    # ser = serial.Serial(port=port, baudrate=9600, timeout=1)
    # ser.flush()

    def update(command, value):
        ser.write((command + value + '\r').encode())
        ser.read_until('\r'.encode())

    def getAmplifierState():
        ser.write('getSTATE\r'.encode())
        returned = ser.read(80)
        ser.flushInput()
        amplifer = AmpliferState(returned)
        return amplifer

    def set_pressure(pressure):
        pass

    def set_voltage(voltage):
        volt = voltage
        update('setVOLT', str(voltage))

    def set_freq(freq):
        update('setFREQ', str(freq))

    def set_operation(conti):
        is_continuous = conti

    def get_load_power():
        amplifier_state = getAmplifierState()
        return  amplifier_state.loadPower

    def get_voltage():
        amplifier_state = getAmplifierState()
        return  amplifier_state.voltage

    def start():
        # update('ENABLE', '')
        if is_pulsed:
            while True:
                print("aww")
                # set_voltage(20)
                # time.sleep(1)
                # set_voltage(0)
                # time.sleep(1)

    def stop():
        print("stop")
        # amplifier_state = getAmplifierState()
        # set_voltage(0)
        # update('DISABLE', '')
