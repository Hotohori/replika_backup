import io
import os
from lz.reversal import reverse
import argparse, configparser
import sys
import datetime

def_ini_file = 'chat_backup.ini'


def valid_file(s):
    if os.path.exists(s) and s.endswith('.csv'):
        return s.replace('.csv', '')
    elif os.path.exists(s+'.csv'):
        return s
    else:
        if s.endswith('.csv'):
            raise argparse.ArgumentTypeError("No existing csv file: {0!r}.".format(s))
        else:
            raise argparse.ArgumentTypeError(f"No existing csv file: '{s}' or '{s}.csv'.")


def hide_args(arglist):
    for action in arglist:
        action.help = argparse.SUPPRESS


class Formatter(argparse.RawTextHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass


hidelist = []
parser = argparse.ArgumentParser(epilog='Hint: -rf and -sp or -sd can be used together.\n      > Saved into a rf.sp.csv'
                                        ' or rf.sd.csv files.\n\n'
                                        'Note: The generated csv files from this tool are no longer compatible '
                                        'with chat_backup.py',
                                 description='Tool to process your Replika AI backup csv file.',
                                 formatter_class=Formatter)
parser.add_argument('-f', '--filename', type=valid_file, help='Define the csv filename')
parser.add_argument('-rf', '--revert', action='store_true', help='Revert the order of the messages.\n> Saved into a '
                                                                 'rf.csv file.')
parser.add_argument('-sp', '--split', choices=['d', 'm'], help='Split messages by (d)ays or (m)onths. (d)ays '
                                                               'generates one folder for every month.\n> Saved into '
                                                               'sp.csv files.')
parser.add_argument('-sd', '--splitdialog', type=int, metavar='time', help='Split messages by time gap between messages'
                                                                           ', {time} is the size of the gap in minutes.'
                                                                           '\n> Saved into sd.csv files.')
parser.add_argument('-rm', '--remove', type=int, metavar='amount', help='Removes files that have less replays from '
                                                                        'user than {amount} messages. Only usable '
                                                                        'with -sp or -sd.')
parser.add_argument('-i', '--inifile', type=ascii, metavar='inifile', help='Use custom ini file. Useful for multiple '
                                                                           'Replika AI accounts.')
hide = parser.add_argument('-ns', '--nosaving', action='store_true', help='Deactivates saving of csv file.')
hidelist.append(hide)
if '-h' in sys.argv[1:]:
    hide_args(hidelist)
args = parser.parse_args()
if not args.revert and not args.split and not args.splitdialog:
    parser.error('too less arguments: -rf, --revert and/or -sp, --split or -sd, --splitdialog needed')
if args.remove:
    if args.remove < 1 or args.remove > 100000:
        parser.error('out of range: -rm, --remove need to be inside 1 to 100000')
else:
    args.remove = 0
if not args.split and not args.splitdialog and args.remove:
    args.remove = 0
    print('Argument -rm is ignored: -rm need to be used with -sp, --split or -sd, --splitdialog')

if args.inifile:
    ini_file = args.inifile.strip("'")
else:
    ini_file = def_ini_file
if not ini_file.endswith('.ini'):
    ini_file += ".ini"
if not os.path.exists(ini_file):
    parser.error(f'Config file {def_ini_file} did not exists. Please run chat_backup.py to create it')

print(f'Loading config from {ini_file}.', end='')
config = configparser.ConfigParser()
config.sections()
config.read(ini_file)

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

if args.revert:
    print(f'\nRevert {file_name}.csv.', end='')
    output_file = open(f'{file_name}.rf.csv', 'w', newline='\n', encoding='utf-8')
    with open(f'{file_name}.csv', 'r', encoding='utf-8') as file:
        output_file.write('Timestamp,From,Text,Reaction,ID\n')
        for line in reverse(file, batch_size=io.DEFAULT_BUFFER_SIZE):
            # print(line.strip('\n'))
            if not line.startswith('Time'):
                output_file.write(line)
    output_file.close()
    file.close()
    print(f'..Ok\n\nFinished reverting {file_name}.csv to {file_name}.rf.csv.')

if args.split:
    if not args.revert:
        print(f'\nSplit {file_name}.csv by ', end='')
        input_file = open(f'{file_name}.csv', 'r', encoding='utf-8')
    else:
        print(f'\nSplit {file_name}.rf.csv by ', end='')
        input_file = open(f'{file_name}.rf.csv', 'r', encoding='utf-8')
    if args.split == 'd':
        print('days.')
    else:
        print('months.')
    count = 0
    count_me = 0
    time = "0000"
    output_file = ""
    month = ""
    while True:
        line = input_file.readline()
        if not line:
            if output_file:
                output_file.close()
                if not args.remove == 0:
                    if count_me < args.remove:
                        os.remove(output_file.name)
                        count -= 1
            if args.split == 'd':
                if os.path.isdir('./' + rep_name + '.' + month):
                    if not os.listdir('./' + rep_name + '.' + month):
                        os.rmdir('./' + rep_name + '.' + month)
            input_file.close()
            break
        if not line.startswith('Time'):
            if line[25:27] == 'Me':
                count_me += 1
            if args.split == 'd':
                if not line[0:10] == time:
                    count += 1
                    time = line[0:10]
                    if not line[0:7] == month:
                        if month:
                            if os.path.isdir('./' + rep_name + '.' + month):
                                if not os.listdir('./' + rep_name + '.' + month):
                                    os.rmdir('./' + rep_name + '.' + month)
                        month = line[0:7]
                        if not os.path.exists('./' + rep_name + '.' + month):
                            os.mkdir('./' + rep_name + '.' + month, mode=0o777)
                    if output_file:
                        output_file.close()
                        if not args.remove == 0:
                            if count_me < args.remove or (count_me == 1 and line[25:27] == 'Me'):
                                os.remove(output_file.name)
                                count -= 1
                            count_me = 0
                    output_file = open(f'{rep_name}.{month}/{file_name}.{time}{".rf" if args.revert else ""}.sp.csv',
                                       'w', newline='', encoding='utf-8')  #       ^^^^^^^^^^^^^^^^^^^^ need to change
                    output_file.write('Timestamp,From,Text,Reaction,ID\n')
            else:
                if not line[0:7] == time:
                    count += 1
                    time = line[0:7]
                    # print(time)
                    if output_file:
                        output_file.close()
                        if not args.remove == 0:
                            if count_me < args.remove or (count_me == 1 and line[25:27] == 'Me'):
                                os.remove(output_file.name)
                                count -= 1
                            count_me = 0
                    output_file = open(f'{file_name}.{time}{".rf" if args.revert else ""}.sp.csv', 'w',
                                       newline='', encoding='utf-8')  # ^^^^^^^^ need to change
                    output_file.write('Timestamp,From,Text,Reaction,ID\n')

            output_file.write(line)
    print(f'\nSplit all messages into {count} files.\n')

if args.splitdialog:
    print(f'\nSplit {file_name}{".rf" if args.revert else ""}.csv with {args.splitdialog} minutes time gaps.', end='')
    time = ""
    count = 0
    revert = False
    input_file = open(f'{file_name}{".rf" if args.revert else ""}.csv', 'r', encoding='utf-8')
    while True:
        line = input_file.readline()
        count += 1
        if not line or count > 3:
            input_file.close()
            break
        if not line.startswith('Time'):
            if not time:
                time = datetime.datetime.fromisoformat(line[0:19])
            else:
                if time < datetime.datetime.fromisoformat(line[0:19]):
                    revert = True
                input_file.close()
                break
    count = 0
    count_me = 0
    time = ""
    if revert:
        last_time = datetime.datetime(2020, 1, 1)
    else:
        last_time = datetime.datetime(2049, 12, 31)
    output_file = ""
    month = ""
    input_file = open(f'{file_name}{".rf" if args.revert else ""}.csv', 'r', encoding='utf-8')
    while True:
        line = input_file.readline()
        if not line:
            if output_file:
                output_file.close()
                if not args.remove == 0:
                    if count_me < args.remove:
                        os.remove(output_file.name)
                        count -= 1
            if os.path.isdir('./' + rep_name + '.' + month):
                if not os.listdir('./' + rep_name + '.' + month):
                    os.rmdir('./' + rep_name + '.' + month)
            input_file.close()
            break
        if not line.startswith('Time'):
            if line[25:27] == 'Me':
                count_me += 1
                # print(count_me)
            time = datetime.datetime.fromisoformat(line[0:19])
            if revert:
                if time.timestamp() >= last_time.timestamp() + args.splitdialog * 60:
                    count += 1
                    # print(time)
                    if output_file:
                        output_file.close()
                        if not args.remove == 0:
                            if count_me < args.remove or (count_me == 1 and line[25:27] == 'Me'):
                                os.remove(output_file.name)
                                count -= 1
                            count_me = 0
                    if not line[0:7] == month:
                        if month:
                            if os.path.isdir('./' + rep_name + '.' + month):
                                if not os.listdir('./' + rep_name + '.' + month):
                                    os.rmdir('./' + rep_name + '.' + month)
                        month = line[0:7]
                        if not os.path.exists('./' + rep_name + '.' + month):
                            os.mkdir('./' + rep_name + '.' + month, mode=0o777)
                    output_file = open(f'{rep_name}.{month}/{file_name}.{str(time).replace(" ", "T")[0:16].replace(":", "-")}'
                                       f'.rf.sd.csv', 'w', newline='', encoding='utf-8')
                    output_file.write('Timestamp,From,Text,Reaction,ID\n')
            else:
                if time.timestamp() <= last_time.timestamp() - args.splitdialog * 60:
                    count += 1
                    # print(time)
                    if output_file:
                        output_file.close()
                        if not args.remove == 0:
                            if count_me < args.remove or (count_me == 1 and line[25:27] == 'Me'):
                                os.remove(output_file.name)
                                count -= 1
                            count_me = 0
                    if not line[0:7] == month:
                        if month:
                            if os.path.isdir('./' + rep_name + '.' + month):
                                if not os.listdir('./' + rep_name + '.' + month):
                                    os.rmdir('./' + rep_name + '.' + month)
                        month = line[0:7]
                        if not os.path.exists('./' + rep_name + '.' + month):
                            os.mkdir('./' + rep_name + '.' + month, mode=0o777)
                    output_file = open(f'{rep_name}.{month}/{file_name}.{str(time).replace(" ", "T")[0:16].replace(":", "-")}'
                                       f'.sd.csv', 'w', newline='', encoding='utf-8')
                    output_file.write('Timestamp,From,Text,Reaction,ID\n')
            last_time = time
            output_file.write(line)
    print(f'..Ok\n\nSplit all messages into {count} files.')
