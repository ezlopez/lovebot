import os
import ast
import glob
import random
import os.path

from WSePaper import WSePaper
from optparse import OptionParser
from pprint import pprint

message_path = '/home/pi/te-amo/messages'
image_path = '/home/pi/te-amo/images/'

if __name__ == '__main__':
    optp = OptionParser()
    optp.add_option('-n', '--newest', help='update to the newest message', action='store_const',
                    dest='newest', const=True, default=False)
    opts, args = optp.parse_args()
    
    # Initialize the screen
    screen = WSePaper()

    if screen.sendHandshake() != 'OK':
        print('Screen did not perform handshake.')
        exit(-1)
        
    screen.clear()
    
    # Get the files in the messages directory
    files = glob.glob(message_path + '/*.txt')

    # Choose which message to display
    if (opts.newest):
        message_file = max(files, key=os.path.getctime)
    else:
        message_file = random.choice(files)
    
    # Read the file contents
    message = open(message_file, 'r')
    message_text = message.read()
    message.close()
    message_list = ast.literal_eval(message_text)
    
    # Set the font if we have text
    if 'text' in message_text:
        screen.setFontSize(WSePaper.FONT_LARGE)
    
    # Display the message contents
    for section in message_list:
        x = 0
        y = 0
        
        # Check for coordinates
        if len(section) >= 3:
            if 'x=' in section[2]:
                x = int(section[2][2:])
            elif 'y=' in section[2]:
                y = int(section[2][2:])
                
        if len(section) >= 4:
            if 'x=' in section[3]:
                x = int(section[3][2:])
            elif 'y=' in section[3]:
                y = int(section[3][2:])
        
        # Output to the screen
        if section[0] == 'text':
            screen.setStorageArea(WSePaper.STORAGE_NAND)
            print('showText ' + section[1], x, y)
            screen.showText(section[1], x, y)
            
        elif section[0] == 'image':
            image_file_path = image_path + section[1]
            if os.path.isfile(image_file_path):
                screen.setStorageArea(WSePaper.STORAGE_SD)
                print('showImage ' + section[1], x, y)
                if not screen.showImage(section[1], x, y):
                    if not screen.sendImageFile(image_file_path):
                        print('Error: Could not send image: ' + image_file_path)
                    elif not screen.showImage(section[1], x, y):
                        print('Error: Could not show image: ' + section[1])
                        exit()
            else:
                print('Error: Image does not exist.')
                exit()
        else:
            pass #error
        
    screen.update()
    
    print('Message successfully updated.')