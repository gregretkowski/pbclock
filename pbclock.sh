cd /home/pi/pbclock
git fetch --all
git reset --hard origin/master
. venv/bin/activate
python3 main.py &
sleep 30
wmctrl -r :ACTIVE: -e 0,0,0,480,320
