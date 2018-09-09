import logging
import os
import pickle
import sys

import numpy as np


def configure_logging():
    logging.basicConfig(stream=sys.stdout, format='%(levelname)s:%(message)s', level=logging.INFO)


def ddict2dict(d):
    for k, v in d.items():
        if isinstance(v, dict):
            d[k] = ddict2dict(v)
    return dict(d)


def linspace(start, stop, num=50):
    """
    Linspace with additional points
    """
    grid = list(np.linspace(start, stop, num))
    step = (stop - start) / (num - 1)
    grid.extend([0.1 * step, 0.5 * step, stop - 0.1 * step, stop - 0.5 * step])
    return sorted(grid)


class PrintOnce:
    def __init__(self):
        self.printed = False

    def __call__(self, message):
        if not self.printed:
            print(message)
            self.printed = True


def load_or_calc_and_save(filename):
    def my_decorator(func):
        def wrapped():
            if os.path.exists(filename):
                print('File exist! Skip calculations')
                with open(filename, 'rb') as f:
                    result = pickle.load(f)
            else:
                result = func()
                with open(filename, 'wb') as f:
                    pickle.dump(result, f)
            return result

        return wrapped

    return my_decorator