'''Client software to read latest azimuth and dome data'''
import socket

IP_ADDRESS_AZ = '161.72.134.70'
PORT_AZ = 9873

class AzClient:
    '''Client class to get azimuth
    '''
    def __init__(self, ip_addr=IP_ADDRESS_AZ, port=PORT_AZ):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._ip_addr = ip_addr
        self._port = port
        self._sock.connect((self._ip_addr, self._port))

    def get_info(self,length=100):
        '''Get angle and speed
        Returns
        -------
        res: float, float
            Response from the server
        '''
        self._sock.send('a#all{}?'.format(length).encode('utf-8'))
        res = self._sock.recv(4096)
        val = [float(x) for x in str(res, encoding='UTF-8').split(':')[-1].split(',')]
        return [str(res, encoding='UTF-8').split(':')[0]]+val

def check_az():
    azc = AzClient()
    date,az,spd = azc.get_info(3000)
    print(date,' azimuth =',az,'deg, speed =',spd,'rpm')
    del azc
    return date, az, spd

IP_ADDRESS_DOME = '161.72.134.68'
PORT_DOME = 50000

class DomeClient:
    '''Client class to read latest elevation data
    '''
    def __init__(self, ip_addr=IP_ADDRESS_DOME, port=PORT_DOME):
        self._ip_addr = ip_addr
        self._port = port

    def get_status(self):
        '''Get status
        Returns
        -------
        res: str
            Response from the server
        '''
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((self._ip_addr, self._port))
        self._sock.send('d#status?'.encode('utf-8'))
        res = self._sock.recv(4096)
        return str(res, encoding='UTF-8')

def check_dome():
    '''Main function'''
    domec = DomeClient()
    ret = domec.get_status()
    print(ret)
    del domec
    return ret


if __name__ == '__main__':
    check_az()
    check_dome()
