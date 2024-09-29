deactivate
sudo apt install python3-pip
python3 -m pip install --user virtualenv Pillow
python3 -m venv env
source env/bin/activate
pip3 install viam-sdk
