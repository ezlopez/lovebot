#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import logging
import getpass
import sleekxmpp
import urllib.request
import subprocess
import os.path
import os
import time
import schedule
import ast

from optparse import OptionParser
from pprint import pprint
from subprocess import PIPE

if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input


class LoveBot(sleekxmpp.ClientXMPP):

    def __init__(self, jid, password, cmd_jid):
        # Initialize the xmpp client
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        self.cmd_jid = cmd_jid

    def start(self, event):
        self.send_presence()
        self.get_roster()

    def message(self, msg):
        fromName = str(msg['from']).split('/')[0]

        if msg['type'] in ('chat', 'normal'):
            if fromName == self.cmd_jid:
                try:
                    command = msg['body'].split(':')[0].strip()
                except:
                    msg.reply('Could not process command').send()
                    return

                if len(msg['body'].split(':')) > 1:
                    try:
                        parameter = ":".join(msg['body'].split(':')[1:]).strip()
                    except:
                        msg.reply('Could not process command parameter.').send()
                        return

                if command == 'ip':
                    ip = urllib.request.urlopen('https://ifconfig.me').read().decode('utf8')
                    msg.reply(ip).send()

                elif command == 'ping':
                    t = self.plugin['xep_0199'].ping(jid='nerdofnerds.com', ifrom='zeyhre@nerdofnerds.com')
                    msg.reply('Ping time: ' + str(t)).send()

                elif command == 'reboot':
                    self.execute_command('sudo shutdown -r', msg)
                    raise KeyboardInterrupt

                elif command == 'kill':
                    msg.reply('Killing process').send()
                    time.sleep(1)
                    os.system('kill $PPID')

                elif command == 'manual update':
                    self.execute_command('git -C /home/pi/te-amo/source pull origin master', msg)
                    msg.reply('Killing process').send()
                    time.sleep(1)
                    os.system('kill $PPID')

                elif command == 'message':
                    if self.valid_message(parameter):
                        filename = '/home/pi/te-amo/messages/' + time.strftime('%Y%m%d-%H%M%S') + '.txt'
                        file = open(filename, 'w+')
                        file.write(parameter)
                        file.close()

                        self.execute_command('python3 /home/pi/te-amo/source/message-updater.py -n', msg)

                    else:
                        msg.reply('Invalid message command.').send()

                elif command == 'image':
                    p_list = parameter.split(' ')

                    if len(p_list) != 2:
                        msg.reply('Invalid image command.').send()
                        return

                    url = p_list[0]
                    img_name = p_list[1].upper()

                    if len(img_name) > 10 or img_name[-4:] != '.BMP':
                        msg.reply('Invalid image command.').send()
                        return

                    if url:
                        filename = '/home/pi/te-amo/images/' + img_name
                        bashCmd = 'curl -f ' + url + ' -o ' + filename
                        self.execute_command(bashCmd, msg)

                elif command == 'bash':
                    bashCmd = parameter

                    if bashCmd:
                        self.execute_command(bashCmd, msg)

                elif command == 'syntax':
                    cmd = parameter

                    if cmd == 'image':
                        msg.reply('image: <url> <image-name>\n'
                                  '<image-name> must be all-caps, less than 11 characters, and end in ".BMP"').send()
                    elif cmd == 'message':
                        msg.reply('message: [(<image-cmd>)(,<text-cmd> ...)]\n'
                                  '<image-cmd> = ["image", "<image-name>"(, "x=<x-coord>", "y=<y-coord>")]\n'
                                  '<text-cmd> = ["text", "<text-to-display>"(, "x=<x-coord>", "y=<y-coord>")]\n\n'
                                  'ex. \'message: [["image", "heart.bmp"], ["text", "Te amo", "x=100", "y=300"]]\'\n'
                                  'Displays image named "heart.bmp" with "Te amo" printed over it at (100, 300).').send()

                elif command == 'help':
                    msg.reply('\nip\n'
                              'ping\n'
                              'reboot\n'
                              'kill\n'
                              'manual update\n'
                              'bash: <command>\n'
                              'message: [(<image-cmd>)(,<text-cmd> ...)]\n'
                              'image: <url> <image-name>\n'
                              'syntax: [image or message]').send()

    def execute_command(self, command, msg=None):
        cp = subprocess.run(command.split(), stdout=PIPE, stderr=PIPE, encoding='utf-8')

        if msg:
            msg.reply('\nOutput: ' + str(cp.stdout) + '\nError: ' + str(cp.stderr)).send()
        else:
            return (cp.stdout, cp.stderr)

    def valid_message(self, message):
        try:
            msg_list = ast.literal_eval(message)
        except:
            return False

        if len(msg_list) == 0:
            return False

        for layer in msg_list:
            if len(layer) < 2:
                return False

            if layer[0] not in ['text', 'image']:
                return False

            if len(layer) >= 3:
                coord = layer[2]
                if len(coord) <= 2 or coord[0:2] not in ['x=', 'y=']:
                    return False
                try:
                    int(coord[2:])
                except:
                    return False

            if len(layer) >= 4:
                coord = layer[3]
                if len(coord) <= 2 or coord[0:2] not in ['x=', 'y=']:
                    return False
                try:
                    int(coord[2:])
                except:
                    return False

        return True


if __name__ == '__main__':
    # Setup the command line arguments.
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR', action='store_const',
                    dest='loglevel', const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG', action='store_const',
                    dest='loglevel', const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM', action='store_const',
                    dest='loglevel', const=5, default=logging.INFO)

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid", help="JID to use")
    optp.add_option("-p", "--password", dest="password", help="password to use")
    optp.add_option('-c', '--cmd-jid', dest='cmd_jid', help='jid of user we accept commands from')
    opts, args = optp.parse_args()

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,#level=logging.DEBUG,#
                        format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        opts.jid = ''
    if opts.password is None:
        opts.password = ''

    lb = LoveBot(opts.jid, opts.password, opts.cmd_jid)
    lb.register_plugin('xep_0030') # Service Discovery
    lb.register_plugin('xep_0004') # Data Forms
    lb.register_plugin('xep_0060') # PubSub
    lb.register_plugin('xep_0198') # Stream management
    lb.register_plugin('xep_0199') # XMPP Ping
    # xmpp.register_plugin('xep_0096') # File Transfer

    # Connect to the XMPP server and start processing XMPP stanzas.
    if lb.connect(reattempt=False):
        lb.plugin['xep_0199'].enable_keepalive(interval=30)
        lb.process(block=False)

    else:
        print("Unable to connect.")
        exit()

    while True:
        time.sleep(1)
