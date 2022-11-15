# replika_backup

This fork contains a python script (chat_backup.py) to backup your Replika AI history log into a csv file on your Computer.
This script provides also some parameters to control the script and can also update an existing backup.

New on this fork is a tool for processing your csv files (chat_csv_tool.py). The script can revert the message order in both
direction (old > new / new > old) and split your messages by days or months and soon by dialogs based on a user definited time gap.

[Setup Guide](SETUP_GUIDE.md)

### Please report any problems with the script over the Issues tab on the top left.
### I can only fix from what I know that it need to be fixed.
------------------------

# Last Update:
- added ".no" to filemane for "new to old" message order what is the standard what you get from the Replika AI servers. So new file ending is ".no.srv".
- chat_csv_tool.py loads now chat_backup.ini config file if -i is no used.
- added new parameter -sd and -rm to chat_csv_tool.py. -sd let you split your csv by minutes time gaps inbetween messages and -rm removes all split files with less than a specific number of user messages.
- added a new parameter -i to load a custom ini file for both scripts. Useful for multiple Replika AI accounts.
- added Replika Name variable to the ini file.
- Variables are now stored in a extra ini file that automatically gets generated when you run the script.
- added first version of chat_csv-tool. Can revert the sorting order of the messages and split it by days/months. Use the -h parameter for help.
- added instructions for Firefox users into the Walkthrough.
- IMPORTANT! Fixed a \n bug inside chat messages that break csv files. You should backup with the newest version again.
- added install_modules.bat for easier installation of needed Python modules.
- added limit date parameter for only backing up messages to a specific date.
- changed the default srv file name in the script to chat_backup.srv.
- added Replika AI server error messages.
- opened the Issues feature of GitHub for bug reporting.
- Updated the Walkthrough with new more helpful pictures.
- improved the script so only the init variable is needed, makes the setup much easier.
- fixed a maybe critical bug, not sure if all messages was backuped before. Suggest to create a new full backup.
- added command line parameter -log for logging directly the messages anonymized from the WebSocket into chat_backup.log.
- some internal improvements and fixes.
