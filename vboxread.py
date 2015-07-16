#! /usr/bin/env python
#
# Run this, passing the VBO filename as an argument.
# Specify one of the options to make it do something.
# --help will give you the details.
#

import collections
import csv
import re
import sys
import click
import colorama
from datetime import datetime, timedelta


class VBoxData:
    """
    A class representing the data read from a .VBO file.
    """
    def __init__(self, from_vbo_file=None):
        """
        Initialise instance, optionbally reading data from
        VBO file object.

        The 'data' field will be populated with a list of namedtuples,
        each of which has float fields based on the column names. So you can
        get, for example, self.data[0].velocity.
        """
        self.creation_date = None
        self.creation_midnight = None
        self.comments = []
        self.headers = []
        self.column_names = []
        self.data = []
        if from_vbo_file:
            self.read_vbo(from_vbo_file)


    def read_vbo(self, from_vbo_file):
        """
        Populate this object by reading the specified VBO file.

        from_vbo_file should be an open file-like object.
        """
        section = None
        for raw_line in from_vbo_file:
            line = raw_line.strip()

            # Start of new section
            m = re.match(r'\[([\s\w)]+)\]', line)
            if m is not None:
                section = m.group(1)

            else:
                # We're within a section
                                
                if (section is None) and line.startswith('File created on'):
                    # Will parse this at some point
                    creation_date = line[16:]
                    self.creation_date = datetime.strptime(creation_date, "%d/%m/%Y @ %H:%M:%S")
                    self.creation_midnight = self.creation_date.replace(hour=0, minute=0, second=0, microsecond=0)

                if line and (section == 'header'):
                    self.headers.append(line)

                if line and (section == 'comments'):
                    self.comments.append(line)

                if line and (section == 'column names'):
                    # To use the columns as field names in named tuples, we need to replace hyphens
                    self.column_names = [c.replace('-','_') for c in line.split()]
                    self.column_name_map = dict([k[::-1] for k in enumerate(self.column_names)])
                    assert(self.column_names[1] == 'time')  # We assume this later
                    assert(self.column_names[2] == 'lat')   # We assume this later
                    assert(self.column_names[3] == 'long')  # We assume this later
                    self.column_names.append('datetime')    # We'll add one of our own
                    VBoxDataTuple = collections.namedtuple('VBoxDataTuple', self.column_names)

                if line and (section == 'data'):
                    # I think data fields are always numbers, but in different formats
                    # We'll treat them as floats for now
                    bits = line.split()
                    fields = [float(f) for f in bits]

                    # Time, however, looks like a float but is HHMMSS.SS
                    tstamp = bits[1]
                    (hrs, mins, secs) = int(tstamp[0:2]), int(tstamp[2:4]), float(tstamp[4:])
                    fields[1] = 3600 * hrs + 60 * mins + secs
                    fields.append( self.creation_midnight.replace(hour = hrs, minute=mins, second=int(secs)) )

                    # And lat and long are in minutes, with west as positive
                    # Convert to conventional degrees
                    fields[2] = float(fields[2])/60.0
                    fields[3] = -1 * float(fields[3])/60.0

                    # If there's no GPS signal, we won't have absolute time
                    # We assume that time=000000.00 indicates the start of useful data
                    if fields[1] == 0.0:
                        self.data = []

                    tup = VBoxDataTuple(*fields)
                    self.data.append(tup)

        self.min_lat = min([d.lat for d in self.data])
        self.max_lat = max([d.lat for d in self.data])
        self.min_long = min([d.long for d in self.data])
        self.max_long = max([d.long for d in self.data])


    def write_csv(self, outfile=sys.stdout):
        """
        Create a CSV file of the data fields.

        out_file should be an open file-like object.
        """
        csv_out =csv.writer(outfile)
        csv_out.writerow(self.column_names)
        for d in self.data:
            csv_out.writerow(d)


    def plot_graph(self):
        """
        Plot some interesting things on a graph.
        """
        # from numpy import *
        import matplotlib.pyplot as plt

        plt.figure(1)

        plt.subplot(211)
        plt.title('Accelerator, brake and speed')
        accel_line, brake_line, speed_line = plt.plot(
            [d.time for d in self.data],   # x axis
            [(d.PedalPos_CH, d.BrakePressure_HS1_CH, d.VehicleSpeed_HS1_CH ) for d in self.data]  # y values
        )
        plt.legend([accel_line, brake_line, speed_line], ['Accel', 'Brake', 'Speed'])

        plt.subplot(212)
        plt.title('Steering')
        plt.xlabel('Time (s)')
        steering_line, indicator_line = plt.plot(
            [d.time for d in self.data],   # x axis
            [(d.SteeringWheelAngle_CH, [0, -100, 100][int(d.DirectionIndicationSwitchHS_CH)]) for d in self.data]  # y values
        )
        plt.axhline()
        plt.ylabel('Deg left')
        plt.legend([steering_line, indicator_line], ['Steering','Indicator'])

        plt.show()


    def plot_track(self):
        """
        Plot location and colour with speed.
        """
        import matplotlib.pyplot as plt
        from matplotlib.transforms import ScaledTranslation

        fig = plt.figure()
        plt.title('Track')
        ax = plt.gca()
        ax.set_axis_bgcolor((0.1,0.1,0.1))
        max_vel = max([d.velocity for d in self.data])
        if max_vel == 0:
            click.echo("No movement detected!", err=True)
            sys.exit(1)

        plt.scatter(
            [d.long for d in self.data],
            [d.lat for d in self.data],
            c=[(d.velocity/max_vel,0.4,1.0-d.velocity/max_vel,1) for d in self.data],
            s=1,
            marker = u'.',
            linewidth=0, edgecolor='none'
        )
 
        plt.axis('equal')  # a degree is a degree

        labels = [
            ('Coventry', -1.510948, 52.407762),
            ('Warwick Uni', -1.5626, 52.3838),
        ]
        # Coventry label
        for l in labels:
            plt.plot(l[1], l[2], marker='+', color='white')
            plt.annotate(l[0], xy=(l[1], l[2]), 
                    xytext=(5,5), textcoords='offset points', color='gray', alpha=0.8)
        
        plt.show()


    def write_gpx(self, outfile=sys.stdout):
        # Get the Jinja template for rendering a GPX file
        from jinja2 import Environment, FileSystemLoader
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template('track.gpx.j2')
        outfile.write( template.render(vboxdata = self) )



@click.command()
@click.option('--graph', '-g', default=False, is_flag=True, help="Draw a pretty plot")
@click.option('--track', '-t', default=False, is_flag=True, help="Draw a map")
@click.option('--gpx',   '-p', default=None, type=click.File('w'), help="Output a GPX file")
@click.option('--csv',   '-c', default=None, type=click.File('w'), help="Output a CSV file")
@click.argument('vbo_file', type=click.File('r'))

def main(graph, track, gpx, csv, vbo_file):
    vbd = VBoxData(vbo_file)
    print >>sys.stderr, len(vbd.data),"points"

    if gpx:
        vbd.write_gpx(gpx)

    if csv:
        vbd.write_csv(csv)

    if graph:
        vbd.plot_graph()

    if track:
        vbd.plot_track()


if __name__ == '__main__':
    main()