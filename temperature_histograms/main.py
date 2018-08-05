"""Visualization of Climate Change extremes via histograms."""
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import numpy as np
import os
import requests
from scipy.misc import imread
import xarray as xr

LOG_FMT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(level=logging.DEBUG, format=LOG_FMT)
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
            with open('{}/{}'.format(savedir, fn), 'wb') as f:
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


def make_plots(fn, animated_gif='giss_histogram.gif',
               start='185001', end='201801'):
    """Create Histograms plot."""

    start = datetime.strptime(start, '%Y%m')
    end = datetime.strptime(end, '%Y%m')
    # plot parameters
    n_bins = 400
    left_line = -2.5
    right_line = 2.5
    min_val = -6
    max_val = 6
    out_dir = './pngs'
    wallpaper = imread('earth.jpg')

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    for file in os.scandir(out_dir):
        os.unlink(file)
    num_cold_points = 0.
    num_hot_points = 0.

    # plot code
    d0 = datetime(1850, 1, 1)
    start_idx = 12 * relativedelta(start, d0).years +\
        relativedelta(start, d0).months
    end_idx = 12 * relativedelta(end, d0).years +\
        relativedelta(end, d0).months
    fn = download_input()
    ds = xr.open_dataset(fn)

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
        n, bins, patches = plt.hist(data, n_bins, facecolor='white',
                                    density=1, zorder=1)

        # plot the vertical lines for mean, median and right/left limits
        plt.axvline(x=left_line, color='white', linestyle='--',
                    linewidth=0.5)
        plt.axvline(x=right_line, color='white', linestyle='--',
                    linewidth=0.5)
        plt.axvline(x=np.mean(data), color='orange', linestyle='-',
                    linewidth=4)

        # Color under the histogram before `left_line` and after `right_line`
        for index, item in enumerate(zip(bins[:-1], n)):
            width = bins[index+1]-bins[index]
            height = n[index]
            if bins[index] < left_line:
                if bins[index+1] > left_line:
                    width = left_line - bins[index]
                xy = (item[0], 0)
                box = Rectangle(xy, width, height, linewidth=1,
                                edgecolor='royalblue', facecolor='royalblue')
                currentAxis = plt.gca()
                currentAxis.add_patch(box)

            if bins[index + 1] >= right_line:
                if bins[index] < right_line:
                    xy = (right_line, 0)
                    width = bins[index + 1] - right_line
                else:
                    xy = (item[0], 0)

                box = Rectangle(xy, width, height, linewidth=1,
                                edgecolor='orangered', facecolor='orangered')
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
        title = 'Monthly Temp Histogram - Data: Berkley Earth'
        plt.title(title)
        font = {'fontname': 'Helvetica'}
        plt.text(min_val + 0.75, 0.9, month.strftime('%Y'),
                 weight='bold', fontsize=24, **font)
        plt.text(min_val + 0.1, 0.9, month.strftime('%b'),
                 fontsize=10, **font)

        # counting and ploting # of data points
        # num_cold_points += data[np.where(data < left_line)].shape[0]
        # num_hot_points += data[np.where(data > right_line)].shape[0]
        # fraction_cold = num_cold_points / data.shape[0]
        # fraction_hot = num_hot_points / data.shape[0]
        # plt.text(min_val + 0.4, 0.6, '# of data points',
        #          color='royalblue')
        # plt.text(min_val + 1.4, 0.55, '{0:.2f}%'.format(fraction_cold),
        # color='royalblue')
        # plt.text(right_line + 0.4, 0.6, '# of data points',
        #          color='orangered')
        # plt.text(right_line + 1.4, 0.55, '{0:.2f}%'.format(fraction_hot),
        # color='orangered')
        out_name = 'plot_{0:07d}.png'.format(t)
        plt.figimage(wallpaper, 0, 0, alpha=0.9, zorder=0)
        plt.savefig('{}/{}'.format(out_dir, out_name), transparent=True)
        # break

    # anim stuff
    if animated_gif:
        logger.info('Generating animated gif %s', animated_gif)
        try:
            cmd = 'convert -delay 10 -loop 0 '\
                '{0}/*png {1}'.format(out_dir, animated_gif)
            os.system(cmd)
        except Exception as exc:
            logger.error('Unable to generate gif. Exception = %s', exc)

    return


if __name__ == '__main__':

    fn = download_input()
    make_plots(fn, animated_gif='giss_histogram.gif',
               start='190001', end='201801')