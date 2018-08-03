import logging
import matplotlib.pyplot as plt
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
    fn = url.split('/')[-1]
    if not os.path.isfile('{}/{}'.format(savedir, fn)):
        logger.debug('attempting to download : %s', url)
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
            logger.debug('Sucessfully saved: %s', fn)
        except Exception as exc:
            logger.error('Unable to save file: %s, exception: %s', fn, exc)
            return None
    else:
        logger.debug('%s already downloaded', url)

    return fn


if __name__ == '__main__':

    download_input()
