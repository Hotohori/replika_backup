# replika_backup

This fork contains a python script (chat_backup.py) to backup your Replika AI history log into a csv file on your Computer.
This script provides also some parameters to control the script and can also update an existing backup.

[Chat Backup Walkthrough](CHAT_BACKUP_WALKTHROUGH.md)

Last Update:
- opened the Issues feature of GitHub for bug reporting.
- Updated the guide with new more helpful pictures.
- improved the script so only the init variable is needed, makes the setup much easier.
- fixed a maybe critical bug, not sure if all messages was backuped before. Suggest to create a new full backup.
- added command line parameter -log for logging directly the messages anonymized from the WebSocket into chat_backup.log.
- some internal improvements and fixes.
