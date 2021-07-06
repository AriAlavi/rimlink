# Rimlink

The purpose of this utility is to sync rimworld mods, updates, and config folders between a host and multiple users. This will help with reduce the frequency of desyncs when using the multiplayer mod. It only works for Windows as I do not have access to a Mac.

#### In order to use:
1. Port forward on port 5002 OR Make use of Hamachi (if making use of Hamachi, use Hamachi's IP and not your own)
2. Put rimlink.exe in your Rimworld directory and run as admin
3. If you generally host the Rimworld server, make sure you say (y)es when asked so
4. After host has the rimlink tool running, then your friends can run the rimlink tool in the same way, but saying (n)o when asked if they host rimworld servers
5. Rimlink will make sure your friend's files and folders are 100% exactly the same as yours. It will download and remove files as needed for that to happen

---
## Syntax
To run rimlink as a non-admin, you should start via command line as follows:
```
rimlink.exe --noadmin # allows running rimlink as not an admin
```

To run rimlink from a custom saved location, you should start via command line as follows:
```
rimlink.exe --noadmin --savedatafolder "your path here wrapped in doublequotes"
```
---



### Update 2021-7-05
* Implemented multi-threading for ~4x faster speed on a 20 thread CPU

### Update 2020-12-21
* Added functionality to skip admin requirement via commandline argument `--noadmin` for users that have saved their game file outside of protected directories
* Added functionality to allow users to add a commandline parameter to specify custom save location via `--savedatafolder "folderpath"`

