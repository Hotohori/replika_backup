import csv
import json
import requests
import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import time
import os
import sys
import argparse

#---------- edit the variables here --------------

init = '' #Insert full init message between single quotes

chat_id = '' #Only left for fallback, you shouldn't need it any longer (this hex number should be always user_id - 1).

file_name = 'replika_chat_backup' #Default backup filename between single quotes, you can also use the -f parameter

#---------- don't edit anything below -----------

python_dict = json.loads(init)
user_id = python_dict['auth']['user_id']
auth_token = python_dict['auth']['auth_token']
device_id = python_dict['auth']['device_id']
if not chat_id:
    chat_id = '%x' % (int(user_id,16)-1)

last_file_id = ""
all_msg_count = 0
error_count = 0

parser = argparse.ArgumentParser(description= f'Backup your Replika AI chat history into a {file_name}.csv file.')
parser.add_argument('-f', '--filename', type=ascii, metavar='filename', help='define the csv filename')
parser.add_argument('-sm', '--showmsgs', action='store_true', help='show received messages')
parser.add_argument('-ws', '--wsdebug', action='store_true', help='WebSocket debug mode')
parser.add_argument('-lm', '--limitmsgs', type=int, metavar='int', help='Limits to {int} messages')
parser.add_argument('-log', '--logging', action='store_true', help='Logging WebSocket messages anonymized to log file')
parser.add_argument('-ns', '--nosaving', action='store_true', help='Deactivates saving of csv file')
args = parser.parse_args()

if args.filename:
    file_name = args.filename.strip(" ' ")
if file_name.endswith('.csv'):
    file_name = file_name.replace('.csv','')

if not args.limitmsgs:
    if os.path.exists(f'{file_name}.csv'):
        with open(f'{file_name}.csv', encoding='UTF-8') as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            
            for row in reader:
                if row[4] != "ID":
                    last_file_id = row[4]
                    csv_file.close()
                    if not args.nosaving:
                        if os.path.exists(f'{file_name}.old.csv'):
                            os.remove(f'{file_name}.old.csv')
                        os.rename(f'{file_name}.csv',f'{file_name}.old.csv')
                    break
    if not args.nosaving:
        if last_file_id:
            output_file = open(f'{file_name}.new.csv','w', newline='', encoding='utf-8')
        else:
            output_file = open(f'{file_name}.csv','w', newline='', encoding='utf-8')
else:
    if not args.nosaving:
        output_file = open(f'{file_name}.limit.csv','w', newline='', encoding='utf-8')     
if not args.nosaving:
    writer = csv.writer(output_file)
    writer.writerow(['Timestamp','From','Text','Reaction','ID'])
else:
    print('\nWarning! No saving /ns mode, no data will be saved, read-only!\n')
if args.logging:
    log_file = open('chat_backup.log','w', newline='\n', encoding='utf-8')

def on_message(ws, message):
    global msg_count
    global all_msg_count
    msg_count = 0
    python_dict = json.loads(message)
    token = python_dict['token']
    event_name = python_dict['event_name']
    if event_name != "history":
        print(f'..Ok')
    if event_name == "init":
        print('Send chat_screen', end='')
        ws.send('{"event_name":"chat_screen","payload":{},"token":"'+str(token)+'","auth":{"user_id":"'+str(user_id)+'","auth_token":"'+str(auth_token)+'","device_id":"'+str(device_id)+'"}}')
        print('.', end='')
        time.sleep(0.25)
    if event_name == "chat_screen":
        print('Send application_started', end='')
        ws.send('{"event_name":"application_started","payload":{},"token":"'+str(token)+'","auth":{"user_id":"'+str(user_id)+'","auth_token":"'+str(auth_token)+'","device_id":"'+str(device_id)+'"}}')
        print('.', end='')
        time.sleep(0.25)
    if event_name == "application_started":
        print('Send app_foreground', end='')
        ws.send('{"event_name":"app_foreground","payload":{},"token":"'+str(token)+'","auth":{"user_id":"'+str(user_id)+'","auth_token":"'+str(auth_token)+'","device_id":"'+str(device_id)+'"}}')
        print('.', end='')
        time.sleep(0.25)
    if event_name == "app_foreground":
        print('Get message history.', end='')
        if args.limitmsgs:
            if args.limitmsgs < 1000:
                ws.send('{"event_name":"history","payload":{"chat_id":"'+str(chat_id)+'","limit":'+str(args.limitmsgs)+'},"token":"'+str(token)+'","auth":{"user_id":"'+str(user_id)+'","auth_token":"'+str(auth_token)+'","device_id":"'+str(device_id)+'"}}')
            else:
                ws.send('{"event_name":"history","payload":{"chat_id":"'+str(chat_id)+'","limit":1000},"token":"'+str(token)+'","auth":{"user_id":"'+str(user_id)+'","auth_token":"'+str(auth_token)+'","device_id":"'+str(device_id)+'"}}')
        else:
            ws.send('{"event_name":"history","payload":{"chat_id":"'+str(chat_id)+'","limit":5},"token":"'+str(token)+'","auth":{"user_id":"'+str(user_id)+'","auth_token":"'+str(auth_token)+'","device_id":"'+str(device_id)+'"}}')
        time.sleep(0.25)
    #Parse History
    if python_dict['event_name'] == "history":        
        if args.logging:
            fmsg = message.replace(auth_token,'##auth_token##')
            fmsg = fmsg.replace(user_id,'##user_id##')
            fmsg = fmsg.replace(chat_id,'##chat_id##')
            fmsg = fmsg.replace(device_id,'##device_id##')
            fmsg = fmsg.replace('%x' % (int(chat_id,16)-1),'##bot_id##')
            log_file.write(fmsg)
        if args.showmsgs or args.wsdebug:
            print('')
        messages = []
        message_reactions = python_dict["payload"]["message_reactions"]
        reactions = {}
        last_message_id = ""
        for message_reaction in message_reactions:
            reaction_id = message_reaction['message_id']
            reaction_type = message_reaction['reaction']
            reactions[reaction_id] = reaction_type
            
        if python_dict['payload']['messages']:
            for i in range(len(python_dict["payload"]["messages"])-1,-1,-1):   
                message = {}
                message['id'] = python_dict["payload"]["messages"][i]["id"]
                message['chat_id'] = python_dict["payload"]["messages"][i]["meta"]["chat_id"]
                sender = python_dict["payload"]["messages"][i]["meta"]["nature"]
                message['timestamp'] = python_dict["payload"]["messages"][i]["meta"]["timestamp"]
                last_message_id = message['id']         
                if last_message_id == last_file_id:
                    ws.close()
                    if args.logging:
                        log_file.close()
                    if not args.nosaving:
                        output_file.close()
                    if msg_count > 0:
                        if not args.nosaving:    
                            with open(f'{file_name}.new.csv', encoding='UTF-8') as mf:
                                data = mf.readlines()
                                mf.close()
                            with open(f'{file_name}.old.csv', encoding='UTF-8') as mf:
                                data2 = mf.readlines()[1:]
                                mf.close()
                            data += data2
                            with open(f'{file_name}.csv', 'w', encoding='UTF-8') as mf:
                                mf.writelines(data)
                                mf.close()
                            quit(f'\n\nBacked up {all_msg_count} messages up to first old ID {last_message_id} from {message["timestamp"]}\n{file_name}.csv > new and old messages\n{file_name}.new.csv > only new messages\n{file_name}.old.csv > only old messages')
                        else:
                            quit(f'\n\nRead {all_msg_count} messages up to first old ID {last_message_id} from {message["timestamp"]} - nothing saved')
                    else:
                        if not args.nosaving:
                            os.remove(f'{file_name}.new.csv')
                            os.rename(f'{file_name}.old.csv',f'{file_name}.csv')
                        quit('\n\nNo new messages since last backup')
                else:
                    msg_count += 1
                    all_msg_count += 1                    
                if sender == "Robot":
                    message['sender'] = "Rep"
                else:
                    message['sender'] = "Me"
                message['text'] = python_dict["payload"]["messages"][i]["content"]["text"]
                try:
                    message['reaction'] = reactions[message['id']]
                except:
                    message['reaction'] = 'None'
                
                if args.showmsgs:
                    print(f"{message['sender']}: {message['text']} {message['reaction']} ({message['timestamp']}) ({message['id']})")
                
                if not args.nosaving:
                    writer.writerow([message['timestamp'], message['sender'], message['text'], message['reaction'], message['id']])
                
                if args.limitmsgs:
                    if args.limitmsgs > 0:
                        if args.limitmsgs == all_msg_count:
                            ws.close()
                            if args.logging:
                                log_file.close()
                            if not args.nosaving:
                                output_file.close()
                                quit(f'..reached message limit\n\nBacked up {all_msg_count} messages\n{file_name}.limit.csv > limited messages')
                            else:
                                quit(f'..reached message limit\n\nRead {all_msg_count} messages')
                        
            if not args.nosaving:
                print(f'..Ok\nSaved {all_msg_count} messages - Get more messages.', end='')
            else:
                print(f'..Ok\nRead {all_msg_count} messages - Get more messages.', end='')
            ws.send('{"event_name":"history","payload":{"chat_id":"'+str(chat_id)+'","limit":1000,"last_message_id":"'+str(last_message_id)+'"},"token":"'+str(token)+'","auth":{"user_id":"'+str(user_id)+'","auth_token":"'+str(auth_token)+'","device_id":"'+str(device_id)+'"}}')
            time.sleep(1)
        else:
            ws.close()
            if args.logging:
                log_file.close()
            if not args.nosaving:
                output_file.close()
                quit(f'..no further messages\n\nBacked up all possible {all_msg_count} messages\n{file_name}.csv > all messages')
            else:
                quit('..no further messages\n\nRead all possible messages - nothing saved')
        
def on_error(ws, error):
    global error_count
    if not repr(error).split('(')[0] == "SystemExit":
        if error_count == 1 or error != "'token'":
            ws.close()
            if args.logging:
                log_file.close()
            if not args.nosaving:
                output_file.close()
                if os.path.exists(f'{file_name}.old.csv'):
                    if os.path.exists(f'{file_name}.new.csv'):
                        os.remove(f'{file_name}.new.csv')
                    os.rename(f'{file_name}.old.csv',f'{file_name}.csv')
            quit(f'\nError: {error}\n')
        error_count += 1

def on_close(ws, close_status_code, close_msg):
    print('Connection closed')

def on_open(ws):
    def run(*args):
        token = ""
        user_id = ""
        auth_token = ""
        chat_id = ""
        device_id = ""
        ws.send(init)
    print('Send init.', end='')
    time.sleep(1)
    thread.start_new_thread(run, ())

if __name__ == "__main__":
    print('Open websocket to your Replika AI')
    websocket.enableTrace(args.wsdebug)
    ws = websocket.WebSocketApp("wss://ws.replika.ai/v17",
                              on_open = on_open,
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.run_forever()
