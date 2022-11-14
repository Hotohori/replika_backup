import csv
import json
import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import time
import os
import argparse, configparser
import datetime

#  Variables are now stored into a "chat_backup.ini" file.
#  If this file did not exist, mostly when you use this script the first
#  time or using -i with a not existing config file, run this script one
#  time and it will get automatically created.

# to run this script use: python chat_backup.py

# this file is from https://github.com/Hotohori/replika_backup

def_ini_file = 'chat_backup.ini'


def valid_date(s):
    try:
        date = datetime.datetime.strptime(s, "%Y.%m.%d")
        if date:
            if datetime.datetime.now(datetime.timezone.utc).timestamp() <= date.timestamp():
                raise argparse.ArgumentTypeError("Need a older date.")
            elif 1612134000 >= date.timestamp():
                raise argparse.ArgumentTypeError("Date too old. Minimum date 2021.02.01")
        return date
    except ValueError:
        raise argparse.ArgumentTypeError("Not a valid date (YYYY.MM.DD): {0!r}.".format(s))


last_file_id = ""
all_msg_count = 0
error_count = 0
limitdate = ""

parser = argparse.ArgumentParser(description=f'Backup your chat history from the Replika AI servers into a csv file. '
                                             f'Abort script with Ctrl+C.')
parser.add_argument('-f', '--filename', type=ascii, metavar='filename', help='Define the csv filename.')
parser.add_argument('-lm', '--limitmsgs', type=int, metavar='int', help='Limits to {int} messages.')
parser.add_argument('-ld', '--limitdate', type=valid_date, metavar='date',
                    help='Backup only until {date}. Format: YYYY.MM.DD')
parser.add_argument('-i', '--inifile', type=ascii, metavar='inifile', help='Use custom ini file. Useful for multiple '
                                                                           'Replika AI accounts.')
parser.add_argument('-md', '--msgdebug', action='store_true', help='Show received messages.')
parser.add_argument('-ws', '--wsdebug', action='store_true', help='WebSocket debug mode.')
parser.add_argument('-log', '--logging', action='store_true', help='Logging WebSocket messages anonymized to log file.')
parser.add_argument('-ns', '--nosaving', action='store_true', help='Deactivates saving of csv file. Useful with -md, '
                                                                   '-ws, -log.')
args = parser.parse_args()

if args.inifile:
    ini_file = args.inifile.strip("'")
else:
    ini_file = def_ini_file
if not ini_file.endswith('.ini'):
    ini_file += ".ini"

if not os.path.exists(ini_file):
    print(f'\nConfig file "{ini_file}" is missing\n\nFile will get created now.', end='')
    with open(ini_file, 'w', encoding='utf-8') as file:
        file.write("[DEFAULT]\n# Name of your Replika. Default: Replika\n\nNAME = Replika\n\n# Filename suffix. It "
                   "will used with NAME to build the Filename for the csv backup file.\n# NAME + SUFFIX. By default it"
                   " will be \"Replika_backup\" what lead into \"Replika_backup.csv\".\n# The -f parameter replace "
                   "NAME + SUFFIX. Default: _backup\n\nSUFFIX = _backup\n\n# Only left for fallback, you should not "
                   "need it any longer. Let it empty.\n# This CHAT_ID hex number should be always user_id - 1 from "
                   "the INIT message.\n\nCHAT_ID = \n\n# Insert here the full init message from your browser behind "
                   "\"INIT = \".\n# Some text editors show some less line breaks inside the init message where\n# "
                   "are none because of the very long line, ignore it, should be fine.\n\nINIT = \n")
        file.close()
        quit(f'..Ok\n\nCreated "{ini_file}" - please edit this file now to use it.')

if args.limitdate:
    limitdate = str(args.limitdate - datetime.timedelta(days=1))[0:10]
print(f'Loading config from {ini_file}.', end='')
config = configparser.ConfigParser()
config.sections()
config.read(ini_file)
init = config['DEFAULT']['INIT'].strip(" \"'")
if not init:
    quit(f'\n\nError: INIT variable not set inside "{ini_file}".')
rep_name = config['DEFAULT']['NAME']
if not rep_name:
    quit(f'\n\nError: NAME variable not set inside {ini_file} or use -f instead.')
if not config['DEFAULT']['SUFFIX']:
    quit(f'\n\nError: SUFFIX variable not set inside {ini_file} or use -f instead.')
if args.filename:
    file_name = args.filename.strip(" '")
else:
    file_name = config['DEFAULT']['NAME'].strip(" \"'")+config['DEFAULT']['SUFFIX'].strip(" \"'")
if file_name.endswith('.csv'):
    file_name = file_name.replace('.csv', '')

python_dict = json.loads(init)
user_id = python_dict['auth']['user_id']
auth_token = python_dict['auth']['auth_token']
device_id = python_dict['auth']['device_id']
chat_id = config['DEFAULT']['CHAT_ID']
if not chat_id:
    chat_id = '%x' % (int(user_id, 16) - 1)
print('..Ok')

if not args.limitmsgs:
    if not limitdate:
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
                            os.rename(f'{file_name}.csv', f'{file_name}.old.csv')
                        break
        if not args.nosaving:
            if last_file_id:
                output_file = open(f'{file_name}.new.csv', 'w', newline='', encoding='utf-8')
            else:
                output_file = open(f'{file_name}.csv', 'w', newline='', encoding='utf-8')
    else:
        if not args.nosaving:
            output_file = open(f'{file_name}.' + str(args.limitdate)[0:10] + '.csv', 'w', newline='', encoding='utf-8')
else:
    if not args.nosaving:
        output_file = open(f'{file_name}.limit.csv', 'w', newline='', encoding='utf-8')
if not args.nosaving:
    writer = csv.writer(output_file)
    writer.writerow(['Timestamp', 'From', 'Text', 'Reaction', 'ID'])
else:
    print('\nWarning! No saving /ns mode, no data will be saved, read-only!\n')
if args.logging:
    log_file = open('chat_backup.log', 'w', newline='\n', encoding='utf-8')


def on_message(ws, message):
    global msg_count
    global all_msg_count
    limit = 1000
    msg_count = 0
    python_dict = json.loads(message)
    token = python_dict['token']
    event_name = python_dict['event_name']
    if event_name != "history":
        print(f'..Ok')
        # if event_name != "init":
        # print(message)
    if event_name == "error":
        ws.close()
        if args.logging:
            log_file.close()
        if not args.nosaving:
            output_file.close()
            if os.path.exists(f'{file_name}.old.csv'):
                if os.path.exists(f'{file_name}.new.csv'):
                    os.remove(f'{file_name}.new.csv')
                os.rename(f'{file_name}.old.csv', f'{file_name}.csv')
        if python_dict['payload']['error_message'].find('Authorization failed') > -1:
            print('\nServer Error: Authorization failed.\n\nHint: The Init variable need to be updated inside '
                  'the script.')
        elif python_dict['payload']['error_message'].find(f'Device {device_id} not found for user') > -1:
            print('\nServer Error: You are not logged in with this device.\n\nHint: The Init variable need to be '
                  'updated inside the script after login.')
        else:
            print('\nServer Error: ' + python_dict['payload']['error_message'])
        quit()
    if event_name == "init":
        print('Send chat_screen', end='')
        ws.send('{"event_name":"chat_screen","payload":{},"token":"' + str(token) + '","auth":{"user_id":"' +
                str(user_id) + '","auth_token":"' + str(auth_token) + '","device_id":"' + str(device_id) + '"}}')
        print('.', end='')
        time.sleep(1)
    if event_name == "chat_screen":
        print('Send application_started', end='')
        ws.send('{"event_name":"application_started","payload":{},"token":"' + str(token) + '","auth":{"user_id":"' +
                str(user_id) + '","auth_token":"' + str(auth_token) + '","device_id":"' + str(device_id) + '"}}')
        print('.', end='')
        time.sleep(1)
    if event_name == "application_started":
        print('Send app_foreground', end='')
        ws.send('{"event_name":"app_foreground","payload":{},"token":"' + str(token) + '","auth":{"user_id":"' +
                str(user_id) + '","auth_token":"' + str(auth_token) + '","device_id":"' + str(device_id) + '"}}')
        print('.', end='')
        time.sleep(1)
    if event_name == "app_foreground":
        print('Get message history.', end='')
        if args.limitmsgs:
            if args.limitmsgs < 1000:
                limit = args.limitmsgs
        elif last_file_id:
            limit = 5
        ws.send('{"event_name":"history","payload":{"chat_id":"' + str(chat_id) + '","limit":' + str(
            limit) + '},"token":"' +
                str(token) + '","auth":{"user_id":"' + str(user_id) + '","auth_token":"' + str(
            auth_token) + '","device_id":"' +
                str(device_id) + '"}}')
        time.sleep(1)
    # Parse History
    if python_dict['event_name'] == "history":
        if args.logging:
            fmsg = message.replace(auth_token, '##auth_token##')
            fmsg = fmsg.replace(user_id, '##user_id##')
            fmsg = fmsg.replace(chat_id, '##chat_id##')
            fmsg = fmsg.replace(device_id, '##device_id##')
            fmsg = fmsg.replace('%x' % (int(chat_id, 16) - 1), '##bot_id##')
            jsfmsg = json.loads(fmsg)
            for i in range(len(jsfmsg["payload"]["messages"]) - 1, -1, -1):
                jsfmsg["payload"]["messages"][i]["meta"]["client_token"] = "##client_token##"
            log_file.write(json.dumps(jsfmsg, indent=4))
        if args.msgdebug or args.wsdebug:
            print('')
        message_reactions = python_dict["payload"]["message_reactions"]
        reactions = {}
        last_message_id = ""
        for message_reaction in message_reactions:
            reaction_id = message_reaction['message_id']
            reaction_type = message_reaction['reaction']
            reactions[reaction_id] = reaction_type

        if python_dict['payload']['messages']:
            for i in range(len(python_dict["payload"]["messages"]) - 1, -1, -1):
                message = {'id': python_dict["payload"]["messages"][i]["id"],
                           'chat_id': python_dict["payload"]["messages"][i]["meta"]["chat_id"]}
                sender = python_dict["payload"]["messages"][i]["meta"]["nature"]
                message['timestamp'] = python_dict["payload"]["messages"][i]["meta"]["timestamp"]
                if limitdate:
                    if message['timestamp'][0:10] == limitdate:
                        ws.close()
                        if args.logging:
                            log_file.close()
                        if not args.nosaving:
                            output_file.close()
                            quit(f'..reached date limit\n\nBacked up {all_msg_count} messages\n{file_name}.' +
                                 str(args.limitdate)[0:10] + '.csv > limited date')
                        else:
                            quit(f'..reached date limit\n\nRead {all_msg_count} messages - nothing saved')
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
                            quit(f'\n\nBacked up {all_msg_count} messages up to first old ID {last_message_id}'
                                 f' from {message["timestamp"]}\n{file_name}.csv > new and old messages\n{file_name}.'
                                 f'new.csv > only new messages\n{file_name}.old.csv > only old messages')
                        else:
                            quit(f'\n\nRead {all_msg_count} messages up to first old ID {last_message_id}'
                                 f' from {message["timestamp"]} - nothing saved')
                    else:
                        if not args.nosaving:
                            os.remove(f'{file_name}.new.csv')
                            os.rename(f'{file_name}.old.csv', f'{file_name}.csv')
                        quit('..Ok\n\nNo new messages since last backup')
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

                if args.msgdebug:
                    print(f"{message['sender']}: {message['text']} {message['reaction']} ({message['timestamp']}) "
                          f"({message['id']})")

                if not args.nosaving:
                    writer.writerow([message['timestamp'], message['sender'], message['text'].replace("\n", "\\n"),
                                     message['reaction'], message['id']])

                if args.limitmsgs:
                    if args.limitmsgs > 0:
                        if args.limitmsgs == all_msg_count:
                            ws.close()
                            if args.logging:
                                log_file.close()
                            if not args.nosaving:
                                output_file.close()
                                quit(f'..reached message limit\n\nBacked up {all_msg_count} messages\n'
                                     f'{file_name}.limit.csv > limited messages')
                            else:
                                quit(f'..reached message limit\n\nRead {all_msg_count} messages - nothing saved')

            if not args.nosaving:
                print(f'..Ok\nSaved {all_msg_count} messages - Get more messages.', end='')
            else:
                print(f'..Ok\nRead {all_msg_count} messages - Get more messages.', end='')
            ws.send(
                '{"event_name":"history","payload":{"chat_id":"' + str(chat_id) + '","limit":1000,"last_message_id":"' +
                str(last_message_id) + '"},"token":"' + str(token) + '","auth":{"user_id":"' + str(user_id) +
                '","auth_token":"' + str(auth_token) + '","device_id":"' + str(device_id) + '"}}')
            time.sleep(1)
        else:
            ws.close()
            if args.logging:
                log_file.close()
            if not args.nosaving:
                output_file.close()
                quit(f'..no further messages\n\nBacked up all possible {all_msg_count} messages\n{file_name}.csv'
                     f' > all messages')
            else:
                quit('..no further messages\n\nRead all possible messages - nothing saved')


def on_error(error):
    global error_count
    if not repr(error).split('(')[0] == "SystemExit":
        if error_count == 2 or error != "'token'":
            ws.close()
            if args.logging:
                log_file.close()
            if not args.nosaving:
                output_file.close()
                if os.path.exists(f'{file_name}.old.csv'):
                    if os.path.exists(f'{file_name}.new.csv'):
                        os.remove(f'{file_name}.new.csv')
                    os.rename(f'{file_name}.old.csv', f'{file_name}.csv')
            quit(f'\n\nError: {error}\n')
        error_count += 1


def on_close():
    print('Connection closed')


def on_open(ws):
    def run(*args):
        token = ""
        user_id = ""
        auth_token = ""
        chat_id = ""
        device_id = ""
        ws.send(init)

    print('..Ok\nSend init.', end='')
    time.sleep(1)
    thread.start_new_thread(run, ())


if __name__ == "__main__":
    print(f'Open websocket to your Replika AI \'{rep_name}\'.', end='')
    websocket.enableTrace(args.wsdebug)
    ws = websocket.WebSocketApp("wss://ws.replika.ai/v17",
                                on_open=on_open,
                                on_message=on_message,
                                # on_error = on_error,
                                on_close=on_close)
    ws.run_forever()
