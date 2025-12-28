# TODO

- [ ] get it working again
- [ ] deployment via github autopull
- [ ] modularize data/display (see spec)

# data/display spec
enhancement to data/display. have one routine grab/scrape all the data. another interacts with the display to display the blocks. maybe a third which handles math

example of usage;
fetch launches; fetch sunset; (and wx); if a launch is within an hour of sunset and sky cover is clear; the 'launch' block turns orange.


### New notes on dev.

   python -m venv .venv


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
