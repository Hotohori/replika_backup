import io
import os
from lz.reversal import reverse
import argparse
import sys


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
parser = argparse.ArgumentParser(epilog='Hint: -rf and -sp can be used together.\n      Saved into a rf.sp.csv files\n'
                                        '\nNote: The generated csv files from this tool are no longer compatible '
                                        'with chat_backup.py',
                                 description='Tool to process your Replika AI backup csv file.',
                                 formatter_class=Formatter)
parser.add_argument('filename', type=valid_file, help='Define the csv filename')
parser.add_argument('-rf', '--revert', action='store_true', help='Revert the order of the messages.\nSaved into a '
                                                                 'rf.csv file')
parser.add_argument('-sp', '--split', choices=['d', 'm'], help='Split messages by (d)ays or (m)onths. (d)ays '
                                                               'generates one folder for every month.\nSaved into a '
                                                               'sp.csv files')
hide = parser.add_argument('-ns', '--nosaving', action='store_true', help='Deactivates saving of csv file')
hidelist.append(hide)
if '-h' in sys.argv[1:]:
    hide_args(hidelist)
args = parser.parse_args()
if not args.revert and not args.split:
    parser.error('too less arguments: -rf, --revert and/or -sp, --split needed')

file_name = args.filename
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
    print(f'..Ok\n\nFinished reverting {file_name}.csv to {file_name}.r.csv.')

if args.split:
    if not args.revert:
        print(f'\nSplit {file_name}.csv by ', end='')
        input_file = open(f'{file_name}.csv', 'r', encoding='utf-8')
    else:
        print(f'\nSplit {file_name}.r.csv by', end='')
        input_file = open(f'{file_name}.rf.csv', 'r', encoding='utf-8')
    if args.split == 'd':
        print('days.')
    else:
        print('months.')
    count = 0
    time = "0000"
    output_file = ""
    month = ""
    while True:
        line = input_file.readline()
        if not line:
            if output_file:
                output_file.close()
            input_file.close()
            break
        if not line.startswith('Time'):
            if args.split == 'd':
                if not line[0:10] == time:
                    count += 1
                    time = line[0:10]
                    if not line[0:7] == month:
                        month = line[0:7]
                        if not os.path.exists('./'+month):
                            os.mkdir('./'+month, mode=0o777)
                    if output_file:
                        output_file.close()
                    output_file = open(f'{month}/{file_name}.{time}{".rf" if args.revert else ""}.sp.csv', 'w',
                                       newline='', encoding='utf-8')
                    output_file.write('Timestamp,From,Text,Reaction,ID\n')
            else:
                if not line[0:7] == time:
                    count += 1
                    time = line[0:7]
                    # print(time)
                    if output_file:
                        output_file.close()
                    output_file = open(f'{file_name}.{time}{".rf" if args.revert else ""}.sp.csv', 'w',
                                       newline='', encoding='utf-8')
                    output_file.write('Timestamp,From,Text,Reaction,ID\n')

            output_file.write(line)
    print(f'\nSplit all messages into {count} files.\n')
