#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Copyright (c) 2018 青岛中怡智能安全研究院有限公司
# All right reserved.
#
# See the README file for information on usage and redistribution.

from __future__ import print_function
import os
import platform
import socket
from socket import AF_INET, SOCK_DGRAM
import time

SERVER_DEFAULT_UDP_PORT = 7777
MAX_MESSAGE_SIZE = 26  # 数据段最大字节数


class EchoServer:
    def __init__(self):
        self.sock_obj = None

    def run(self, bind_ip, bind_port=SERVER_DEFAULT_UDP_PORT):
        """ Run echo server

        :type bind_ip: str
        :type bind_port: int
        """
        try:
            self.sock_obj = socket.SocketType(AF_INET, SOCK_DGRAM)
        except IOError as e:
            print("Failed to create socket: %s" % e.strerror)
            raise RuntimeError('Can not create socket object')

        try:
            self.sock_obj.bind((bind_ip, bind_port))
        except IOError as e:
            errno = e.errno
            print("Error %d: Failed to bind UDP port %d" % (errno, bind_port))
            if 'Windows' == platform.system():
                os.system('net helpmsg ' + str(errno))
                MSDN_URL = 'https://msdn.microsoft.com/library/windows/desktop/ms740668%28v%3Dvs.85%29.aspx'
                print('For more information, see MSDN page:')
                print(MSDN_URL)
            else:
                print(e.strerror)
            self.cleanup()
            raise RuntimeError('Can not bind UDP port')
        except:
            print('Other unexcepted error happened during bind()!')
            raise

        default_timeout = 10.0  # in seconds
        data_buf = bytearray(4096)
        max_buffer_size = len(data_buf)
        import select
        while True:
            socks_incomming, socks_outgoing, errors = select.select([self.sock_obj.fileno()], [], [], default_timeout)
            if len(socks_incomming) <= 0:
                print('Heartbeat at %s' % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
                continue
            # When an UDP packet arrives:
            try:
                data_len, peer_sock_addr = self.sock_obj.recvfrom_into(data_buf)
                if data_len > MAX_MESSAGE_SIZE:
                    # Warning: Long messages should be truncated. Drop the extra bytes.
                    data_len = MAX_MESSAGE_SIZE
                # Send back the data:
                self.sock_obj.sendto(buffer(data_buf, 0, data_len), peer_sock_addr)
            except IOError as e:
                errno = e.errno
                print("Error %d" % (errno))
                print("Debug: max_buffer_size=%d" % (max_buffer_size))
                if 'Windows' == platform.system():
                    os.system('net helpmsg ' + str(errno))

    def cleanup(self):
        print('Cleanning up...')
        if self.sock_obj:
            self.sock_obj.close()
            print('Socket closed successfully.')
        self.sock_obj = None


def main():
    port = 7778
    print('Server will run on UDP port %d' % port)

    server = EchoServer()
    try:
        server.run('0.0.0.0', port)
    except KeyboardInterrupt:
        print('Caught a Ctrl-C KeyboardInterrupt (SIGINT). Do some clean-ups before exit...')
    except RuntimeError:
        print('RuntimeError happened!')
    else:
        print('Other error happened')
    finally:
        server.cleanup()


if '__main__' == __name__:
    main()
