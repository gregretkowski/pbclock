# TODO

- [x] get it working again
- [ ] update pi to use new wifi network
- [ ] deployment via github autopull
- [x] modularize data/display (see spec)

# data/display spec
enhancement to data/display. have one routine grab/scrape all the data. another interacts with the display to display the blocks. maybe a third which handles math

example of usage;
fetch launches; fetch sunset; (and wx); if a launch is within an hour of sunset and sky cover is clear; the 'launch' block turns orange.


### New notes on dev.

   python -m venv .venv
   # any changes to requrements.txt
   uv pip install -r requirements.txt
   python main.py

## Testing

Run tests with:
```bash
python -m unittest test_main -v
```

The tests use mocking to avoid making actual HTTP requests. All external API calls and web scraping are mocked, so tests run quickly and don't require network access.


# Notes on dev

installed LCD-show.
had to add some magic lines to config.txt (what?)
had to 'rotate 180'


{'mission': 'Starlink Group 8-11', 'launcher': 'Falcon 9 Block 5 | SpaceX', 'location': 'Cape Canaveral SFS, Florida, USA', 'datetime': 'Wed, Sep 4, 2024, 05:59 AM PDT' }


https://api.tidesandcurrents.noaa.gov/api/prod//datagetter?&station=9410230&date=today&units=english&datum=MLLW&product=water_level&time_zone=LST_LDT&format=json&application=NOS.COOPS.TAC.COOPSMAP&interval=


https://api.tidesandcurrents.noaa.gov/api/prod//datagetter?&station=9410230&date=latest&units=english&datum=MLLW&product=water_level&time_zone=LST_LDT&format=json&application=NOS.COOPS.TAC.COOPSMAP&interval=

{"error": {"message":" Wrong Date: The supported Date values are: latest, recent, or today. "}}


https://api.tidesandcurrents.noaa.gov/api/prod//datagetter?&station=9410230&range=2&units=english&datum=MLLW&product=water_level&time_zone=LST_LDT&format=json&application=NOS.COOPS.TAC.COOPSMAP


This is how to setup the pi to start a single X app (kiosk mode):
https://github.com/ugotapi/calendarpi/blob/main/1-calendarpi.sh


##### Pi stuff

pi start x with a logged in user.

the user's .xinitrc contains `/home/pi/pbclock/pbclock.sh`
the system has python3-pyqt5 package installed

we have cloned pbclock into /home/pi/pbclock
the startup script will fetch the latest changes upstream and
start the app

