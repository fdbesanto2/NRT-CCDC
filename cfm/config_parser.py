import difflib
import os

import numpy as np
import six
import sklearn.externals.joblib as joblib
import yaml



def convert_config(cfg):
    """ Convert some configuration values to different values
        Author: Chris Holden
    Args:
        cfg (dict): dict: dict of sub-dicts, each sub-dict containing
            configuration keys and values pertinent to a process or algorithm
    Returns:
        dict: configuration dict with some items converted to different objects
    Raises:
        KeyError: raise KeyError if configuration file is not specified
            correctly
    """
    # Expand min/max values to all bands
    n_bands = cfg['dataset']['n_bands']
    mins, maxes = cfg['dataset']['min_values'], cfg['dataset']['max_values']
    if isinstance(mins, (float, int)):
        cfg['dataset']['min_values'] = np.asarray([mins] * n_bands)
    else:
        if len(mins) != n_bands:
            raise ValueError('Dataset minimum values must be specified for '
                             '"n_bands" (got %i values, needed %i)' %
                             (len(mins), n_bands))
        cfg['dataset']['min_values'] = np.asarray(mins)

    if isinstance(maxes, (float, int)):
        cfg['dataset']['max_values'] = np.asarray([maxes] * n_bands)
    else:
        if len(maxes) != n_bands:
            raise ValueError('Dataset maximum values must be specified for '
                             '"n_bands" (got %i values, needed %i)' %
                             (len(maxes), n_bands))
        cfg['dataset']['max_values'] = np.asarray(maxes)


    # Unpickle refit objects
    refit = dict(prefix=[], prediction=[], prediction_object=[])
    cfg['YATSM']['refit'] = refit

    return cfg


def parse_config_file(config_file):
    """ Parse YAML config file
    Args:
        config_file (str): path to YAML config file
    Returns:
        dict: dict of sub-dicts, each sub-dict containing configuration keys
            and values pertinent to a process or algorithm. Pickled `sklearn`
            models will be loaded and returned as an object within the dict
    Raises:
        KeyError: raise KeyError if configuration file is not specified
            correctly
    """
    #import pdb; pdb.set_trace()
    with open(config_file) as f:
        cfg = yaml.safe_load(f)
    cfg = expand_envvars(cfg)

    # Ensure algorithm & prediction sections are specified
    if 'YATSM' not in cfg:
        raise KeyError('YATSM must be a section in configuration YAML file')

    if 'algorithm' not in cfg['YATSM']:
        raise KeyError('YATSM section does not declare an algorithm')
    algo = cfg['YATSM']['algorithm']
    if algo not in cfg:
        raise KeyError('Algorithm specified (%s) is not parameterized in '
                       'configuration file' % algo)

    if 'prediction' not in cfg['YATSM']:
        raise KeyError('YATSM section does not declare a prediction method')
    if cfg['YATSM']['prediction'] not in cfg:
        raise KeyError('Prediction method specified (%s) is not parameterized '
                       'in configuration file' % cfg['YATSM']['prediction'])

    # Add in dummy phenology and classification dicts if not included
    if 'phenology' not in cfg:
        cfg['phenology'] = {'enable': False}

    if 'classification' not in cfg:
        cfg['classification'] = {'training_image': None}

    return convert_config(cfg)



def expand_envvars(d):
    """ Recursively convert lookup that look like environment vars in a dict
    This function things that environmental variables are values that begin
    with '$' and are evaluated with ``os.path.expandvars``. No exception will
    be raised if an environment variable is not set.
    Args:
        d (dict): expand environment variables used in the values of this
            dictionary
    Returns:
        dict: input dictionary with environment variables expanded
    """
    _d = d.copy()
    for k, v in six.iteritems(_d):
        if isinstance(v, dict):
            _d[k] = expand_envvars(v)
        elif isinstance(v, str):
            _d[k] = os.path.expandvars(v)
        elif isinstance(v, (list, tuple)):
            n_v = []
            for _v in v:
                if isinstance(_v, str):
                    _v = os.path.expandvars(_v)
                n_v.append(_v)
            _d[k] = n_v
    return _d
