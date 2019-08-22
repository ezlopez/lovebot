import serial
from time import sleep

class WSePaper(object):
    FRAME_HEADER = b'\xa5'
    FRAME_FOOTER = b'\xcc\x33\xc3\x3c'
    HEADER_LENGTH = 1
    COMMAND_LENGTH = 1
    LENGTH_LENGTH = 2
    FOOTER_LENGTH = 4
    CHECK_LENGTH = 1
    
    FONT_SMALL = b'\x01'
    FONT_MED   = b'\x02'
    FONT_LARGE = b'\x03'
    
    commands = {'handshake':      b'\x00', 'setBaud':        b'\x01',
                'getBaud':        b'\x02', 'getStorageArea': b'\x06',
                'setStorageArea': b'\x07', 'sleep':          b'\x08',
                'refreshDisplay': b'\x0A', 'getDisplayDir':  b'\x0C',
                'setDisplayDir':  b'\x0D', 'importFontLib':  b'\x0E',
                'importImage':    b'\x0F', 'setColor':       b'\x10',
                'getColor':       b'\x11', 'getFontSize':    b'\x1C',
                'setFontSize':    b'\x1E', 'drawPoint':      b'\x20',
                'drawLine':       b'\x22', 'fillRect':       b'\x24',
                'drawRect':       b'\x25', 'drawCircle':     b'\x26',
                'fillCircle':     b'\x27', 'drawTriangle':   b'\x28',
                'fillTriangle':   b'\x29', 'clearScreen':    b'\x2E',
                'showText':       b'\x30', 'showImage':      b'\x70'}
    
    def __init__(self):
        self.serial = serial.Serial('/dev/ttyS0', 115200, timeout=1)
        
    def calcPacketLen(self, data):
        '''
        Calculate the total length of the packet and returns it as a number
        (Formatted like the packet requires!).
        '''
        return (self.HEADER_LENGTH + self.LENGTH_LENGTH +
                self.COMMAND_LENGTH + len(data) +
                self.FOOTER_LENGTH + self.CHECK_LENGTH).to_bytes(2, byteorder='big')
    
    def calcChecksum(self, message):
        '''
        Creates a checksum by xor-ing every byte of (byte string) data.
        '''
        checksum = 0
        for byte in message:
            checksum = checksum ^ byte
        return checksum.to_bytes(1, byteorder='big')
    
    def formatMessage(self, command, data=b''):
        length = self.calcPacketLen(data)
        packet = self.FRAME_HEADER + length + command + data + self.FRAME_FOOTER
        packet = packet + self.calcChecksum(packet)
        return packet
    
    def sendMessage(self, message):
        if self.serial:
            self.serial.write(message)
        else:
            print('Serial line is not open')
            
    def recvMessage(self):
        if self.serial:
            message = ''
            
            while True:
                char = self.serial.read()
                if char:
                    message += char.decode('utf-8')
                else:
                    return message
        else:
            print('Serial line is not open')
    
    def sendHandshake(self):
        packet = self.formatMessage(self.commands['handshake'])
        self.sendMessage(packet)
        return self.recvMessage()
    
    def showText(self, text, xCoord, yCoord):
        data  = xCoord.to_bytes(2, byteorder='big') + yCoord.to_bytes(2, byteorder='big')
        data += text.encode('utf-8') + b'\x00'
        packet = self.formatMessage(self.commands['showText'], data)
        self.sendMessage(packet)
        return self.recvMessage()
        
    def setFontSize(self, size):
        packet = self.formatMessage(self.commands['setFontSize'], size)
        self.sendMessage(packet)
        return self.recvMessage()
        
    def clear(self):
        packet = self.formatMessage(self.commands['clearScreen'])
        self.sendMessage(packet)
        return self.recvMessage()
        
    def update(self):
        packet = self.formatMessage(self.commands['refreshDisplay'])
        self.sendMessage(packet)