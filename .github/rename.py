import os

if os.name == "nt":
    os.system('move build\\main.exe build\\onedisc.exe')
else:
    os.system('mv build/main.bin build/onedisc')

