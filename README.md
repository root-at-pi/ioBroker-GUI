# ioBroker-GUI

## Abhänige Pakete
### Debian
```
apt install git python3 python3-venv python3-pip
```

## Installation
```
git clone https://github.com/root-at-pi/ioBroker-GUI.git
cd ioBroker-GUI/
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

## Start
```bash
#!/bin/bash
cd ioBroker-GUI/
source venv/bin/activate
python3 main.py
```
