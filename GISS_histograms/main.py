from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import numpy as np
import os
import requests
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


def make_plots(fn):
    """Create Histograms plot."""

    # plot parameters
    n_bins = 300
    left_line = -2.5
    right_line = 2.5
    min_val = -10
    max_val = 10
    out_dir = './pngs'

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # plot code
    d0 = datetime(1850, 1, 1)
    fn = download_input()
    ds = xr.open_dataset(fn)

    plt.style.use('seaborn-notebook')
    plt.tight_layout(True)

    for t in range(ds['time'].shape[0]):
        month = d0 + relativedelta(months=t)
        logger.info('Generating frame for date: %s', month.strftime('%b %Y'))

        data = ds['temperature'][t, :, :].values.flatten()
        data = data[~np.isnan(data)]
        n, bins, patches = plt.hist(data, n_bins, facecolor='gray',
                                    alpha=0.45, density=1)
        plt.axvline(x=left_line, color='k', linestyle='--', linewidth=0.5)
        plt.axvline(x=right_line, color='k', linestyle='--', linewidth=0.5)
        plt.fill_between(bins[1:], 0, n, where=bins[1:] < left_line,
                         color='blue')
        plt.fill_between(bins[1:], 0, n, where=bins[1:] > right_line,
                         color='red')

        plt.yticks([])
        plt.xticks(fontsize=8)
        plt.xlim(min_val, max_val)

        plt.ylabel('Frequency of ocurrence')
        plt.xlabel('Temperature Anomalies ($^\circ$C)')

        plt.title(month.strftime('%b %Y'))
        out_name = 'plot_{0:07d}.png'.format(t)
        plt.savefig('{}/{}'.format(out_dir, out_name))
        plt.close('all')
        # if t == 10:
        #     break

    logger.info('Generating animated gif')
    try:
        cmd = 'convert -delay 20 -loop 0 {0}/*png myimage.gif'.format(out_dir)
        os.system(cmd)
    except Exception as exc:
        logger.error('Unable to generate gif. Exception = %s', exc)

    return


# def create_animation(fn):
#     imagemagick_path = '/usr/local/bin/convert'
#     plt.rcParams["animation.convert_path"] = imagemagick_path
#     fig = plt.figure()
#     plots = make_plots(fn)
#     anim = ArtistAnimation(fig, plots)
#     writer = ImageMagickFileWriter()
#     anim.save('plot.gif', writer=writer)


if __name__ == '__main__':

    fn = download_input()
    make_plots(fn)
