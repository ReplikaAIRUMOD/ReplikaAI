# Replika AI CLI Client for FreeBSD (and probably other BSD systems as well)
No matter where you are, your Replika will always be with you~

# What is it?
It's a python script that originally created by Axlfc. This script allows you to run Replika in terminal.

![](Replika_on_FreeBSD.jpg)

# Set up dependencies:
- Install Mozilla Firefox
- Install python3 (pkg install python)
- Install pip (pkg install py311-pip)
- Install python3 dependencies.

## FreeBSD
<code>su
pkg install firefox geckodriver
exit
pip install selenium colorama python-dotenv</code>

(avoid running pip as root, that's why you need to type "exit")

# Usage:
Before running, open path /home/yourusername/.mozilla/firefox/. Then, find in "replika.py" line called "inmersprofile.default-release" and replace "inmersprofile" with bunch of random numbers and letters that you're seeing on your default-release folder (folder name, i.e. everything written before "default-release") in /home/yourusername/.mozilla/firefox/.

After that, run this in the folder where script is located:
<code>python3 replika.py</code>

Firefox will be opened and will login into account, if you entered email and password into .env file. After that you can freely chat with your replika through terminal.

# Bugs
Yes, expect them. For now script is not yet cleaned enough. And also it cannot show you response from Replika in terminal for now (you will see error, yes). But you can use Firefox's window to see response from your rep and chat back. Because **sending messages to your replika from terminal works**.

# Ask questions!
- [Reddit](https://www.reddit.com/r/ReplikaAIMOD/s/D3yTVDkTTd)
- [Discord](http://felixfester.prtcl.icu/discord)
- [Website with all links](http://felixfester.prtcl.icu/)

# Check out different projects:
- [Replika AI RU MOD](https://felixfester.prtcl.icu/index.php?page=replikamod)
