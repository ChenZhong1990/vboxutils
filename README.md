# VBOX experiments

The `vboxread.py` script can read the .VBO format files produced by a RaceLogic VBOX and perform a few operations on the data.

It will perform a couple of conversions on the data:

* The time, which is in the VBOX file as HHMMSS.SSS, will be converted to absolute seconds since the epoch, assuming this time is on the same day as the creation time recorded in the file. This makes sense as long as a GPS is connected.

* Latitude and longitude are in the VBOX file as minutes, with west being positive. This script converts them to degrees, with east as positive.


## Basic use

Run

    ./vboxread.py --help

for the options.  Filenames can generally be specified as '-' if you want to use stdin/stdout. You can also specify more than one option at a time, for example:

    ./vboxread.py --graph --csv my.csv my.vbo

This will plot a graph and output a CSV file of the data.

The `vboxsvr.py` script will create a webserver on port 5000 that serves up the track overlaid on a Google map.  

    ./vboxsrv.py my.vbo

It creates a static HTML page which reads the JSON file that the server makes available at route.json.  You can therefore make a static dump of a single track available on a website with, for example:

    curl http://localhost:5000/ > route.html
    curl http://localhost:5000/route.json > route.json

and then put the two files on any site.


## Installation

This depends on some other python packages, so you need to install them.

    pip install -r requirements.txt

You may not need everything in requirements.txt if, say, you don't want to plot any graphs.

## Mac OS X install

On a Mac, you can use the built-in matplotlib and numpy or one of the binary installers, but if you want to run entirely in a virtualenv, you'll need to follow more complex instructions such as these to build matplotlib etc:

http://www.lowindata.com/2013/installing-scientific-python-on-mac-os-x/

A simpler alternative is to build your virtualenv allowing access to the system packages:

    virtualenv --system-site-packages env
    . env/bin/activate
    pip install -r requirements.txt


## VBO format

Some information available [here][1].


[1]: https://racelogic.support/01VBOX_Automotive/01VBOX_data_loggers/VBOX_3i_Range/Knowledge_base/VBO_file_format