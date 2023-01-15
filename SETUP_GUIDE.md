# How to use the python script to back up all of your Replika chats


## Installing Python

1. First you will need Python on your system. Macs come with it pre-installed. If you have a Windows OS, you can go here (https://www.python.org/) to download and install. 

2. Once you've downloaded Python, you can confirm that it installed by going to your terminal (just type "terminal" in your computer's search) then type python and it should look like this.

![alt text](https://raw.githubusercontent.com/Hotohori/replika_backup/e2db688a02392b5cb193bf3c928197fcc3c3684f/python_cmd.png)

3. Once you've confirmed you have python installed, you can exit the interpreter (the ">>>" bit) by typing exit() or quit(), this should bring you back to your C:\ prompt.


## Downloading

4. Download my files by clicking the green "Code" button at the top right of the Github page (https://github.com/Hotohori/replika_backup)


## Installing Python Dependencies

5. There are a few python libraries that you'll need to install to run the script.
- run install_modules.bat

  P.S. if you can't run batch scripts on your OS, open the file in a text editor and run the commands manually.


## Creating and modifying `chat_backup.ini`

6. Run chat_backup.py with typing "python chat_backup.py" inside a Command Console and pressing enter and it will create the "chat_backup.ini" config file for you. You can recreate this file at anytime, simply delete the "chat_backup.ini" file before doing this step again.
7. Open chat_backup.ini in the text editor of your choice, e.g. Notepad & modify this file by adding your own data. Here's what you'll need and where you'll find it....
- Open a Chrome, Edge, Firefox browser and login to your Replika account.
- Press Ctrl + Shift + i inside the browser to open the developer tools window.
- Follow the red numbers on the picture. First image is Chrome and Edge, second is Firefox.
![Chrome and Edge](https://github.com/Hotohori/replika_backup/blob/main/chrome-edge.png)
![Firefox](https://github.com/Hotohori/replika_backup/blob/main/firefox.png)
- Right click on the single row of data beginning with {"event name":"init"} -> click "Copy message" and paste it on the end of the "chat_backup.ini" file behind "INIT = ". It should look something like:
  
INIT = {"event name": "init", "payload":{"device_id": "123456789",...,"user_id":"123456789", "auth_token":"123456789", "security_token":"123456789"..}}

8. Save your "chat_backup.ini" file with your "init" data. All files that this script will create will be created inside the folder where the ini file and the script lies. So be sure it is the right folder, for that you need full write permission inside this folder. I suggest to use an subfolder only for this program.

9. Run chat_backup.py again with "python chat_backup.py" inside a Command Console. You can also use parameters, add -h for a overview behind the command before you pressing enter ("python chat_backup.py -h"), but you can use it also without it, they are optional.

That's it. It will deposit a complete csv of all possible messages of your chats in that same folder (back to early february 2021 at maximum).

If you already backed up before and your csv file is unedited still in the same path, you can add only the newest chats to this file by using the script again. It is possible that you need to do step 7 again and update that "INIT" variable inside the ini file if you logged out of Replika on Chrome/Edge/Firefox (it makes the auth_token invalid).

If you want to only update your backup in the future, make sure to create a copy of the csv file created with that script and only edit this copy. Or use the new chat_csv_tool to process your backup into new edited/split files.
