cd /home/pi/pbclock
git fetch --all
git reset --hard origin/master
if [ ! -d "venv" ]; then
    echo "venv directory not found, creating virtual environment..."
    python3 -m venv venv
fi
. venv/bin/activate
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi

python3 main.py &
sleep 30
wmctrl -r :ACTIVE: -e 0,0,0,480,320
