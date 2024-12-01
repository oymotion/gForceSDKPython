# !/usr/bin/python
# -*- coding:utf-8 -*-

import struct
import threading
import time
from datetime import datetime, timedelta

import asyncio
from bleak import BleakClient, BleakScanner, BleakGATTCharacteristic


class GF_RET_CODE(int):

    # Method returns successfully.
    GF_SUCCESS = 0

    # Method returns with a generic error.
    GF_ERROR = 1

    # Given parameters are not match required.
    GF_ERROR_BAD_PARAM = 2

    # Method call is not allowed by the inner state.
    GF_ERROR_BAD_STATE = 3

    # Method is not supported at this time.
    GF_ERROR_NOT_SUPPORT = 4

    # Hub is busying on device scan and cannot fulfill the call.
    GF_ERROR_SCAN_BUSY = 5

    # Insufficient resource to perform the call.
    GF_ERROR_NO_RESOURCE = 6

    # A preset timer is expired.
    GF_ERROR_TIMEOUT = 7

    # Target device is busy and cannot fulfill the call.
    GF_ERROR_DEVICE_BUSY = 7

    # The retrieving data is not ready yet
    GF_ERROR_NOT_READY = 9


class CommandType(int):
    CMD_GET_PROTOCOL_VERSION = 0x00
    CMD_GET_FEATURE_MAP = 0x01
    CMD_GET_DEVICE_NAME = 0x02
    CMD_GET_MODEL_NUMBER = 0x03
    CMD_GET_SERIAL_NUMBER = 0x04
    CMD_GET_HW_REVISION = 0x05
    CMD_GET_FW_REVISION = 0x06
    CMD_GET_MANUFACTURER_NAME = 0x07
    CMD_GET_BOOTLOADER_VERSION = 0x0A
    CMD_GET_BATTERY_LEVEL = 0x08
    CMD_GET_TEMPERATURE = 0x09
    CMD_POWEROFF = 0x1D
    CMD_SWITCH_TO_OAD = 0x1E
    CMD_SYSTEM_RESET = 0x1F
    CMD_SWITCH_SERVICE = 0x20
    CMD_SET_LOG_LEVEL = 0x21
    CMD_SET_LOG_MODULE = 0x22
    CMD_PRINT_KERNEL_MSG = 0x23
    CMD_MOTOR_CONTROL = 0x24
    CMD_LED_CONTROL_TEST = 0x25
    CMD_PACKAGE_ID_CONTROL = 0x26
    CMD_SEND_TRAINING_PACKAGE = 0x27
    CMD_GET_ACCELERATE_CAP = 0x30
    CMD_SET_ACCELERATE_CONFIG = 0x31
    CMD_GET_GYROSCOPE_CAP = 0x32
    CMD_SET_GYROSCOPE_CONFIG = 0x33
    CMD_GET_MAGNETOMETER_CAP = 0x34
    CMD_SET_MAGNETOMETER_CONFIG = 0x35
    CMD_GET_EULER_ANGLE_CAP = 0x36
    CMD_SET_EULER_ANGLE_CONFIG = 0x37
    CMD_GET_QUATERNION_CAP = 0x38
    CMD_SET_QUATERNION_CONFIG = 0x39
    CMD_GET_ROTATION_MATRIX_CAP = 0x3A
    CMD_SET_ROTATION_MATRIX_CONFIG = 0x3B
    CMD_GET_GESTURE_CAP = 0x3C
    CMD_SET_GESTURE_CONFIG = 0x3D
    CMD_GET_EMG_RAWDATA_CAP = 0x3E
    CMD_SET_EMG_RAWDATA_CONFIG = 0x3F
    CMD_GET_MOUSE_DATA_CAP = 0x40
    CMD_SET_MOUSE_DATA_CONFIG = 0x41
    CMD_GET_JOYSTICK_DATA_CAP = 0x42
    CMD_SET_JOYSTICK_DATA_CONFIG = 0x43
    CMD_GET_DEVICE_STATUS_CAP = 0x44
    CMD_SET_DEVICE_STATUS_CONFIG = 0x45
    CMD_GET_EMG_RAWDATA_CONFIG = 0x46
    CMD_SET_DATA_NOTIF_SWITCH = 0x4F
    # Partial command packet, format: [CMD_PARTIAL_DATA, packet number in reverse order, packet content]
    CMD_PARTIAL_DATA = 0xFF


# Response from remote device
class ResponseResult(int):
    RSP_CODE_SUCCESS = 0x00
    RSP_CODE_NOT_SUPPORT = 0x01
    RSP_CODE_BAD_PARAM = 0x02
    RSP_CODE_FAILED = 0x03
    RSP_CODE_TIMEOUT = 0x04
    # Partial packet, format: [RSP_CODE_PARTIAL_PACKET, packet number in reverse order, packet content]
    RSP_CODE_PARTIAL_PACKET = 0xFF


class DataNotifFlags(int):
    # Data Notify All Off
    DNF_OFF = 0x00000000
    # Accelerate On(C.7)
    DNF_ACCELERATE = 0x00000001
    # Gyroscope On(C.8)
    DNF_GYROSCOPE = 0x00000002
    # Magnetometer On(C.9)
    DNF_MAGNETOMETER = 0x00000004
    # Euler Angle On(C.10)
    DNF_EULERANGLE = 0x00000008
    # Quaternion On(C.11)
    DNF_QUATERNION = 0x00000010
    # Rotation Matrix On(C.12)
    DNF_ROTATIONMATRIX = 0x00000020
    # EMG Gesture On(C.13)
    DNF_EMG_GESTURE = 0x00000040
    # EMG Raw Data On(C.14)
    DNF_EMG_RAW = 0x00000080
    # HID Mouse On(C.15)
    DNF_HID_MOUSE = 0x00000100
    # HID Joystick On(C.16)
    DNF_HID_JOYSTICK = 0x00000200
    # Device Status On(C.17)
    DNF_DEVICE_STATUS = 0x00000400
    # Device Log On(C.18)
    DNF_LOG = 0x00000800
    # EMG Gesture with strength On(C.19)
    DNF_EMG_GESTURE_STRENGTH = 0x00001000
    # Data Notify All On
    DNF_ALL = 0xFFFFFFFF


class ProfileCharType(int):
    PROF_SIMPLE_DATA = 0  # simple profile: data char
    PROF_DATA_CMD = 1  # data profile: cmd char
    PROF_DATA_NTF = 2  # data profile：nty char
    PROF_OAD_IDENTIFY = 3  # OAD profile：identify char
    PROF_OAD_BLOCK = 4  # OAD profile：block char
    PROF_OAD_FAST = 5  # OAD profile：fast char


class NotifDataType(int):
    NTF_ACC_DATA = 0x01
    NTF_GYO_DATA = 0x02
    NTF_MAG_DATA = 0x03
    NTF_EULER_DATA = 0x04
    NTF_QUAT_FLOAT_DATA = 0x05
    NTF_ROTA_DATA = 0x06
    NTF_EMG_GEST_DATA = 0x07
    NTF_EMG_ADC_DATA = 0x08
    NTF_HID_MOUSE = 0x09
    NTF_HID_JOYSTICK = 0x0A
    NTF_DEV_STATUS = 0x0B
    NTF_LOG_DATA = 0x0C  # Log data
    # Partial packet, format: [NTF_PARTIAL_DATA, packet number in reverse order, packet content]
    NTF_PARTIAL_DATA = 0xFF


class LogLevel(int):
    LOG_LEVEL_DEBUG = 0x00
    LOG_LEVEL_INFO = 0x01
    LOG_LEVEL_WARN = 0x02
    LOG_LEVEL_ERROR = 0x03
    LOG_LEVEL_FATAL = 0x04
    LOG_LEVEL_NONE = 0x05


class BluetoothDeviceState(int):
    disconnected = 0
    connected = 1


SERVICE_GUID = "0000ffd0-0000-1000-8000-00805f9b34fb"
CMD_NOTIFY_CHAR_UUID = "f000ffe1-0451-4000-b000-000000000000"
DATA_NOTIFY_CHAR_UUID = "f000ffe2-0451-4000-b000-000000000000"


class CommandCallbackTableEntry:
    def __init__(self, _cmd, _timeoutTime, _cb):
        self._cmd = _cmd
        self._timeoutTime = _timeoutTime
        self._cb = _cb


class GForceProfile:
    def __init__(self):
        self.device = None
        self.state = BluetoothDeviceState.disconnected
        self.cmdCharacteristic = None
        self.notifyCharacteristic = None
        self.timer = None
        self.cmdMap = {}
        self.mtu = None
        self.cmdForTimeout = -1
        self.incompleteCmdRespPacket = []
        self.lastIncompleteCmdRespPacketId = 0
        self.incompleteNotifPacket = []
        self.lastIncompleteNotifPacketId = 0
        self.onData = None
        self.lock = threading.Lock()

    def handle_disconnect(_: BleakClient):
        for task in asyncio.all_tasks():
            task.cancel()

    # Establishes a connection to the Bluetooth Device.
    async def connect(self, addr):
        self.device = BleakClient(addr, disconnected_callback=self.handle_disconnect)
        await self.device.connect()

        print("connection succeeded.")

        # TODO：set mtu?

        self.mtu = self.device.mtu_size
        print(f"mtu:{self.mtu}")

        self.state = BluetoothDeviceState.connected

        # self.cmdCharacteristic = self.getCharacteristic(self.device, CMD_NOTIFY_CHAR_UUID)
        self.cmdCharacteristic = CMD_NOTIFY_CHAR_UUID
        # self.notifyCharacteristic = self.getCharacteristic(self.device, DATA_NOTIFY_CHAR_UUID)
        self.notifyCharacteristic = DATA_NOTIFY_CHAR_UUID

        await self.device.start_notify(self.cmdCharacteristic, self._onResponse)

    # Connect the bracelet with the strongest signal
    async def connectByRssi(self, timeout, name_prefix="", min_rssi=-128):
        scan_result = await self.scan(timeout, name_prefix, min_rssi)

        rssi_devices = {}

        for dev in scan_result:
            rssi_devices[dev["rssi"]] = dev["address"]

        rssi = rssi_devices.keys()
        dev_addr = rssi_devices[max(rssi)]

        # connect the bracelet
        self.device = BleakClient(dev_addr, disconnected_callback=self.handle_disconnect)
        await self.device.connect()
        print("connection succeeded")

        # TODO：set mtu?

        self.mtu = self.device.mtu_size
        print("mtu:{1}".format(self.mtu))

        self.state = BluetoothDeviceState.connected

        # self.cmdCharacteristic = self.getCharacteristic(self.device, CMD_NOTIFY_CHAR_UUID)
        self.cmdCharacteristic = CMD_NOTIFY_CHAR_UUID
        # self.notifyCharacteristic = self.getCharacteristic(self.device, DATA_NOTIFY_CHAR_UUID)
        self.notifyCharacteristic = DATA_NOTIFY_CHAR_UUID

        await self.device.start_notify(self.cmdCharacteristic, self._onResponse)

    async def scan(self, timeout, name_prefix="", min_rssi=-128):
        # Scan for devices
        scanner = BleakScanner(service_uuids=[SERVICE_GUID])
        await scanner.start()
        time.sleep(timeout)
        await scanner.stop()

        scan_result = []
        i = 1

        for v in scanner.discovered_devices_and_advertisement_data.values():
            dev = v[0]
            advData = v[1]

            if (dev.name is not None) and dev.name.startswith(name_prefix) and (advData.rssi >= min_rssi):
                print("Filtered device %s (%s), RSSI=%d dB" % (dev.address, dev.name, advData.rssi))
                scan_result.append({"index": i, "name": dev.name, "address": dev.address, "rssi": advData.rssi})
                i += 1

        return scan_result

    # Disconnect from device
    async def disconnect(self):
        if self.timer != None:
            self.timer.cancel()
        self.timer = None
        # Close the listenThread

        if self.state == BluetoothDeviceState.disconnected:
            return True
        else:
            await self.device.disconnect()
            self.state == BluetoothDeviceState.disconnected

    # Set data notification flag
    async def setDataNotifSwitch(self, flags, cb, timeout):
        # Pack data
        data = []
        data.append(CommandType.CMD_SET_DATA_NOTIF_SWITCH)
        data.append(0xFF & (flags))
        data.append(0xFF & (flags >> 8))
        data.append(0xFF & (flags >> 16))
        data.append(0xFF & (flags >> 24))
        data = bytes(data)

        def temp(resp, respData):
            if cb != None:
                cb(resp)

        # Send data
        return await self.sendCommand(ProfileCharType.PROF_DATA_CMD, data, True, temp, timeout)

    # async def switchToOAD(self,cb,timeout):
    #     # Pack data
    #     data = []
    #     data.append(CommandType.CMD_SWITCH_TO_OAD)
    #     data = bytes(data)
    #     def temp(resp,respData):
    #         if cb != None:
    #             cb(resp,None)

    #     # Send data
    #     return await self.sendCommand(ProfileCharType.PROF_DATA_CMD,data,True,temp,timeout)

    async def powerOff(self, timeout):
        # Pack data
        data = []
        data.append(CommandType.CMD_POWEROFF)
        data = bytes(data)

        def temp(resp, respData):
            pass

        # Send data
        return await self.sendCommand(ProfileCharType.PROF_DATA_CMD, data, True, temp, timeout)

    async def systemReset(self, timeout):
        # Pack data
        data = []
        data.append(CommandType.CMD_SYSTEM_RESET)
        data = bytes(data)

        def temp(resp, respData):
            pass

        # Send data
        return await self.sendCommand(ProfileCharType.PROF_DATA_CMD, data, True, temp, timeout)

    async def setMotor(self, switchStatus, cb, timeout):
        data = []
        data.append(CommandType.CMD_MOTOR_CONTROL)

        tem = 0x01 if switchStatus else 0x00
        data.append(tem)
        data = bytes(data)

        def temp(resp, respData):
            if cb != None:
                cb(resp)

        # send data
        return await self.sendCommand(ProfileCharType.PROF_DATA_CMD, data, True, temp, timeout)

    async def setLED(self, switchStatus, cb, timeout):
        data = []
        data.append(CommandType.CMD_LED_CONTROL_TEST)

        tem = 0x01 if switchStatus else 0x00
        data.append(tem)
        data = bytes(data)

        def temp(resp, respData):
            if cb != None:
                cb(resp)

        # send data
        return await self.sendCommand(ProfileCharType.PROF_DATA_CMD, data, True, temp, timeout)

    # Get controller firmware version
    async def setLogLevel(self, logLevel, cb, timeout):
        # Pack data
        data = []
        data.append(CommandType.CMD_SET_LOG_LEVEL)
        data.append(0xFF & logLevel)
        data = bytes(data)

        def temp(resp, respData):
            if cb != None:
                cb(resp)

        # Send data
        return await self.sendCommand(ProfileCharType.PROF_DATA_CMD, data, True, temp, timeout)

    # Set Emg Raw Data Config
    async def setEmgRawDataConfig(self, sampRate, channelMask, dataLen, resolution, cb, timeout):
        # Pack data
        data = b""
        data += struct.pack("<B", CommandType.CMD_SET_EMG_RAWDATA_CONFIG)
        data += struct.pack("<H", sampRate)
        data += struct.pack("<H", channelMask)
        data += struct.pack("<B", dataLen)
        data += struct.pack("<B", resolution)

        def temp(resp, raspData):
            if cb != None:
                cb(resp)

        # Send data
        return await self.sendCommand(ProfileCharType.PROF_DATA_CMD, data, True, temp, timeout)

    # Get Emg Raw Data Config
    async def getEmgRawDataConfig(self, cb, timeout):
        # Pack data
        data = []
        data.append(CommandType.CMD_GET_EMG_RAWDATA_CONFIG)
        data = bytes(data)

        def temp(resp, respData):
            if cb != None:
                if resp != ResponseResult.RSP_CODE_SUCCESS:
                    cb(resp, None, None, None, None)
                elif len(respData) == 6:
                    sampRate, channelMask, dataLen, resolution = struct.unpack_from("@HHBB", respData)
                cb(resp, sampRate, channelMask, dataLen, resolution)

        return await self.sendCommand(ProfileCharType.PROF_DATA_CMD, data, True, temp, timeout)

    async def getFeatureMap(self, cb, timeout):
        # Pack data
        data = []
        data.append(CommandType.CMD_GET_FEATURE_MAP)
        data = bytes(data)

        def temp(resp, respData):
            if cb != None:
                if resp != ResponseResult.RSP_CODE_SUCCESS:
                    cb(resp, None)
                elif len(respData) == 4:
                    featureMap = struct.unpack("@I", respData)[0]
                    cb(resp, featureMap)

        return await self.sendCommand(ProfileCharType.PROF_DATA_CMD, data, True, temp, timeout)

    # Get controller firmware version
    async def getControllerFirmwareVersion(self, cb, timeout):
        # Pack data
        data = []
        data.append(CommandType.CMD_GET_FW_REVISION)
        data = bytes(data)

        def temp(resp, respData):
            if cb != None:
                if resp != ResponseResult.RSP_CODE_SUCCESS:
                    cb(resp, None)
                else:
                    if len(respData) > 4:
                        firmwareVersion = respData.decode("ascii")
                    else:
                        firmwareVersion = ""
                        for i in respData:
                            firmwareVersion += str(i) + "."
                        firmwareVersion = firmwareVersion[0 : len(firmwareVersion)]
                    cb(resp, firmwareVersion)

        return await self.sendCommand(ProfileCharType.PROF_DATA_CMD, data, True, temp, timeout)

    async def sendCommand(self, profileCharType, data, hasResponse, cb, timeout):
        if hasResponse and cb != None:
            cmd = data[0]

            self.lock.acquire()

            if cmd in self.cmdMap.keys():
                self.lock.release()
                return GF_RET_CODE.GF_ERROR_DEVICE_BUSY
            self.cmdMap[cmd] = CommandCallbackTableEntry(cmd, datetime.now() + timedelta(milliseconds=timeout), cb)
            self._refreshTimer()
            self.lock.release()

        if profileCharType == ProfileCharType.PROF_DATA_CMD:
            if self.cmdCharacteristic == None:
                return GF_RET_CODE.GF_ERROR_BAD_STATE
            else:
                if len(data) > self.mtu:
                    contentLen = self.mtu - 2
                    packetCount = (len(data) + contentLen - 1) // contentLen
                    startIndex = 0
                    buf = []

                    for i in range(packetCount - 1, 0, -1):
                        buf.append(CommandType.CMD_PARTIAL_DATA)
                        buf.append(i)
                        buf += data[startIndex : startIndex + contentLen]
                        startIndex += contentLen
                        # self.send_queue.put_nowait(buf)
                        await self.device.write_gatt_char(self.cmdCharacteristic, buf)
                        buf.clear()
                    # Packet end
                    buf.append(CommandType.CMD_PARTIAL_DATA)
                    buf.append(0)
                    buf += data[startIndex:]
                    # self.send_queue.put_nowait(buf)
                    await self.device.write_gatt_char(self.cmdCharacteristic, buf)
                else:
                    # self.send_queue.put_nowait(data)
                    await self.device.write_gatt_char(self.cmdCharacteristic, data)

                return GF_RET_CODE.GF_SUCCESS
        else:
            return GF_RET_CODE.GF_ERROR_BAD_PARAM

    # Refresh time,need external self.lock
    def _refreshTimer(self):
        def cmp_time(cb):
            return cb._timeoutTime

        if self.timer != None:
            self.timer.cancel()

        self.timer = None
        cmdlist = self.cmdMap.values()

        if len(cmdlist) > 0:
            cmdlist = sorted(cmdlist, key=cmp_time)

        # Process timeout entries
        timeoutTime = None
        listlen = len(cmdlist)

        for i in range(listlen):
            timeoutTime = cmdlist[0]._timeoutTime
            print("_" * 40)
            print("system time : ", datetime.now())
            print("timeout time: ", timeoutTime)
            print("\ncmd: {0}, timeout: {1}".format(hex(cmdlist[0]._cmd), timeoutTime < datetime.now()))
            print("_" * 40)

            if timeoutTime > datetime.now():
                self.cmdForTimeout = cmdlist[0]._cmd
                ms = int((timeoutTime.timestamp() - datetime.now().timestamp()) * 1000)

                if ms <= 0:
                    ms = 1
                self.timer = threading.Timer(ms / 1000, self._onTimeOut)
                self.timer.start()

                break

            cmd = cmdlist.pop(0)

            if cmd._cb != None:
                cmd._cb(ResponseResult.RSP_CODE_TIMEOUT, None)

    async def startDataNotification(self, onData):
        self.onData = onData

        try:
            await self.device.start_notify(self.notifyCharacteristic, self._handleDataNotification)
            success = True
        except:
            success = False

        if success:
            return GF_RET_CODE.GF_SUCCESS
        else:
            return GF_RET_CODE.GF_ERROR_BAD_STATE

    async def stopDataNotification(self):
        try:
            await self.device.stop_notify(self.notifyCharacteristic)
            success = True
        except:
            success = False

        if success:
            return GF_RET_CODE.GF_SUCCESS
        else:
            return GF_RET_CODE.GF_ERROR_BAD_STATE

    def _handleDataNotification(self, characteristic: BleakGATTCharacteristic, data: bytearray):
        fullPacket = []

        if len(data) >= 2:
            if data[0] == NotifDataType.NTF_PARTIAL_DATA:
                if self.lastIncompleteNotifPacketId != 0 and self.lastIncompleteNotifPacketId != data[1] + 1:
                    print(
                        "Error:lastIncompleteNotifPacketId:{0},current packet id:{1}".format(
                            self.lastIncompleteNotifPacketId, data[1]
                        )
                    )
                    # How to do with packet loss?
                    # Must validate packet len in onData callback!

                if self.lastIncompleteNotifPacketId == 0 or self.lastIncompleteNotifPacketId > data[1]:
                    # Only accept packet with smaller packet num
                    self.lastIncompleteNotifPacketId = data[1]
                    self.incompleteNotifPacket += data[2:]

                    if self.lastIncompleteNotifPacketId == 0:
                        fullPacket = self.incompleteNotifPacket
                        self.incompleteNotifPacket = []

            else:
                fullPacket = data

        if len(fullPacket) > 0:
            self.onData(fullPacket)

    # Command notification callback
    def _onResponse(self, characteristic, data):
        print("_onResponse: characteristic= {0}, data= {1}".format(characteristic, data))

        fullPacket = []

        if len(data) >= 2:
            if data[0] == ResponseResult.RSP_CODE_PARTIAL_PACKET:
                if self.lastIncompleteCmdRespPacketId != 0 and self.lastIncompleteCmdRespPacketId != data[1] + 1:
                    print(
                        "Error: _lastIncompletePacketId:{0}, current packet id:{1}".format(
                            self.lastIncompleteCmdRespPacketId, data[1]
                        )
                    )

                if self.lastIncompleteCmdRespPacketId == 0 or self.lastIncompleteCmdRespPacketId > data[1]:
                    self.lastIncompleteCmdRespPacketId = data[1]
                    self.incompleteCmdRespPacket += data[2:]
                    print("_incompleteCmdRespPacket 等于 ", self.incompleteCmdRespPacket)

                    if self.lastIncompleteCmdRespPacketId == 0:
                        fullPacket = self.incompleteCmdRespPacket
                        self.incompleteCmdRespPacket = []
            else:
                fullPacket = data

        if fullPacket != None and len(fullPacket) >= 2:
            resp = fullPacket[0]
            cmd = fullPacket[1]

            # Delete command callback table entry & refresh timer's timeout

            self.lock.acquire()

            if cmd > 0 and self.cmdMap.__contains__(cmd):
                cb = self.cmdMap[cmd]._cb

                del self.cmdMap[cmd]

                self._refreshTimer()

                if cb != None:
                    cb(resp, fullPacket[2:])

            self.lock.release()

    # Timeout callback function
    def _onTimeOut(self):
        print("_onTimeOut: _cmdForTimeout={0}, time={1}".format(self.cmdForTimeout, datetime.now()))

        # Delete command callback table entry & refresh timer's timeout

        cb = None
        self.lock.acquire()

        if self.cmdForTimeout > 0 and self.cmdMap.__contains__(self.cmdForTimeout):
            cb = self.cmdMap[self.cmdForTimeout]._cb
            del self.cmdMap[self.cmdForTimeout]

        self._refreshTimer()

        self.lock.release()

        if cb != None:
            cb(ResponseResult.RSP_CODE_TIMEOUT, None)
