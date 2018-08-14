"""Visualization of temperature extremes via histograms."""
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
from matplotlib.patches import Patch
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import numpy as np
import os
import requests
from scipy.misc import imread
import xarray as xr

LOG_FMT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FMT)
logger = logging.getLogger()


def download_input():
    """Download data used in plot."""
    url = 'http://berkeleyearth.lbl.gov/auto/Global/Gridded/'\
          'Land_and_Ocean_LatLong1.nc'
    savedir = './data'
    fn = '{}/{}'.format(savedir, url.split('/')[-1])
    if not os.path.isfile(fn):
        logger.info('attempting to download : %s', url)
        try:
            r = requests.get(url)
        except Exception as exc:
            logger.error('Unable to download from: %s, exception: %s',
                         url,
                         exc)
            return None

        logger.debug('saving file : %s', fn)
        try:
            with open('{}'.format(fn), 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
            logger.info('Sucessfully saved: %s', fn)
        except Exception as exc:
            logger.error('Unable to save file: %s, exception: %s', fn, exc)
            return None
    else:
        logger.info('%s already downloaded', url)

    return fn


def make_plots(fn, animated_gif='histogram.gif', start='185001', end='201801'):
    """Create Histograms plot."""
    # plot parameters
    n_bins = 400
    left_line = -2.5
    right_line = 2.5
    min_val = -6
    max_val = 6
    cold_color = 'royalblue'
    hot_color = 'orangered'
    out_dir = './pngs'
    wallpaper = imread('earth.jpg')

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    for file in os.scandir(out_dir):
        os.unlink(file)
    num_cold_points = 0.
    num_hot_points = 0.
    plt.rcParams['font.weight'] = 'bold'
    # plot code
    ds = xr.open_dataset(fn)
    d0 = datetime(1850, 1, 1)

    if start == 'start':
        start = d0
    else:
        start = datetime.strptime(start, '%Y%m')
    if end == 'end':
        end = d0 + relativedelta(months=ds.coords['time'].size)
    else:
        end = datetime.strptime(end, '%Y%m')

    start_idx = 12 * relativedelta(start, d0).years +\
        relativedelta(start, d0).months
    end_idx = 12 * relativedelta(end, d0).years +\
        relativedelta(end, d0).months

    for t in range(start_idx, end_idx):
        plt.close('all')
        plt.style.use('dark_background')
        plt.tight_layout(True)

        month = d0 + relativedelta(months=t)
        logger.info('Generating frame for date: %s', month.strftime('%b %Y'))

        # load data
        data = ds['temperature'][t, :, :].values.flatten()
        data = data[~np.isnan(data)]

        # plot
        n, bins, patches = plt.hist(data, n_bins, facecolor='dimgray',
                                    density=1, zorder=1)

        # plot the vertical lines for mean, median and right/left limits
        plt.axvline(x=left_line, color='white', linestyle='--',
                    linewidth=0.5)
        plt.axvline(x=right_line, color='white', linestyle='--',
                    linewidth=0.5)
        plt.axvline(x=np.mean(data), color='orange', linestyle='-',
                    linewidth=4, label='Mean')

        # Color under the histogram before `left_line` and after `right_line`
        for index, item in enumerate(zip(bins[:-1], n)):
            width = bins[index+1]-bins[index]
            height = n[index]
            if bins[index] < left_line:
                if bins[index+1] > left_line:
                    width = left_line - bins[index]
                xy = (item[0], 0)
                box = Rectangle(xy, width, height, linewidth=1,
                                edgecolor=cold_color, facecolor=cold_color)
                currentAxis = plt.gca()
                currentAxis.add_patch(box)

            if bins[index + 1] >= right_line:
                if bins[index] < right_line:
                    xy = (right_line, 0)
                    width = bins[index + 1] - right_line
                else:
                    xy = (item[0], 0)

                box = Rectangle(xy, width, height, linewidth=1,
                                edgecolor=hot_color, facecolor=hot_color)
                currentAxis = plt.gca()
                currentAxis.add_patch(box)

        # some plot configuration
        plt.ylim([0, 1])
        plt.yticks(fontsize=8)
        plt.xticks(fontsize=8)
        plt.xlim(min_val, max_val)
        # some labeling
        plt.ylabel('Frequency of ocurrence')
        plt.xlabel('Temperature Anomalies ($^\circ$C)')
        title = 'Monthly Temp Histogram \n Data: Berkley Earth'
        plt.title(title)
        plt.text(min_val + 0.8, 0.9, month.strftime('%Y'),
                 weight='bold', fontsize=24)
        plt.text(min_val + 0.1, 0.9, month.strftime('%b'),
                 fontsize=10)

        # counting and ploting frequency bars
        num_cold_points += data[np.where(data < left_line)].shape[0]
        num_hot_points += data[np.where(data > right_line)].shape[0]
        pie_slices = [num_cold_points, num_hot_points]
        pie_colors = [cold_color, hot_color]

        hot_patch = Patch(color=hot_color, label='Warm Events')
        cold_patch = Patch(color=cold_color, label='Cold Events')
        mean_patch = Patch(color='orange', label='Mean')

        plt.legend(handles=[hot_patch, cold_patch, mean_patch],
                   loc='upper right')

        plt.axes([.09, .31, .3, .3], facecolor='k')
        plt.pie(pie_slices, colors=pie_colors,
                autopct='%1.1f%%', startangle=90.)
        plt.title('Accumulated \nFrequencies')
        plt.axis('equal')

        out_name = 'plot_{0:04d}.jpg'.format(t)
        plt.figimage(wallpaper, 0, 0, alpha=0.9, zorder=0, resize=(800, 600))
        plt.savefig('{}/{}'.format(out_dir, out_name), transparent=True,
                    dpi=80, rasterized=True)

    # anim stuff
    if animated_gif:
        logger.info('Generating animated gif %s', animated_gif)
        try:
            cmd = 'convert -delay 10 -loop 0 -geometry 680x420 '\
                '{0}/*jpg {1}'.format(out_dir, animated_gif)
            os.system(cmd)
        except Exception as exc:
            logger.error('Unable to generate gif. Exception = %s', exc)

    return


if __name__ == '__main__':

    fn = download_input()
    make_plots(fn, animated_gif='histogram.gif',
               start='196901', end='end')
