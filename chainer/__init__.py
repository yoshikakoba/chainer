import collections
import os
import threading
import warnings

from chainer import _version
from chainer import configuration  # NOQA
from chainer import cuda  # NOQA
from chainer import dataset  # NOQA
from chainer import datasets  # NOQA
from chainer import function  # NOQA
from chainer import function_hook  # NOQA
from chainer import function_hooks  # NOQA
from chainer import function_node  # NOQA
from chainer import functions  # NOQA
from chainer import initializer  # NOQA
from chainer import initializers  # NOQA
from chainer import iterators  # NOQA
from chainer import link  # NOQA
from chainer import links  # NOQA
from chainer import optimizer  # NOQA
from chainer import optimizers  # NOQA
from chainer import reporter  # NOQA
from chainer import serializer  # NOQA
from chainer import serializers  # NOQA
from chainer import training  # NOQA
from chainer import variable  # NOQA


# import class and function
from chainer.configuration import config  # NOQA
from chainer.configuration import global_config  # NOQA
from chainer.configuration import using_config  # NOQA
from chainer.function import force_backprop_mode  # NOQA
from chainer.function import Function  # NOQA
from chainer.function import FunctionAdapter  # NOQA
from chainer.function import no_backprop_mode  # NOQA
from chainer.function_hook import FunctionHook  # NOQA
from chainer.function_node import FunctionNode  # NOQA
from chainer.function_node import grad  # NOQA
from chainer.functions import array  # NOQA
from chainer.functions.math import basic_math  # NOQA
from chainer.initializer import Initializer  # NOQA
from chainer.link import Chain  # NOQA
from chainer.link import ChainList  # NOQA
from chainer.link import Link  # NOQA
from chainer.optimizer import GradientMethod  # NOQA
from chainer.optimizer import Optimizer  # NOQA
from chainer.optimizer import UpdateRule  # NOQA
from chainer.reporter import DictSummary  # NOQA
from chainer.reporter import get_current_reporter  # NOQA
from chainer.reporter import report  # NOQA
from chainer.reporter import report_scope  # NOQA
from chainer.reporter import Reporter  # NOQA
from chainer.reporter import Summary  # NOQA
from chainer.serializer import AbstractSerializer  # NOQA
from chainer.serializer import Deserializer  # NOQA
from chainer.serializer import Serializer  # NOQA
from chainer.variable import as_variable  # NOQA
from chainer.variable import Parameter  # NOQA
from chainer.variable import Variable  # NOQA


from chainer import _environment_check


# Check environment conditions
_environment_check.check()


__version__ = _version.__version__

_thread_local = threading.local()


def get_function_hooks():
    try:
        ret = _thread_local.function_hooks
    except AttributeError:
        ret = collections.OrderedDict()
        _thread_local.function_hooks = ret
    return ret


global_config.debug = bool(int(os.environ.get('CHAINER_DEBUG', '0')))
global_config.cudnn_deterministic = False
global_config.enable_backprop = True
global_config.keep_graph_on_report = bool(int(
    os.environ.get('CHAINER_KEEP_GRAPH_ON_REPORT', '0')))
global_config.train = True
global_config.type_check = bool(int(os.environ.get('CHAINER_TYPE_CHECK', '1')))
global_config.use_cudnn = os.environ.get('CHAINER_USE_CUDNN', 'auto')
global_config.use_cudnn_tensor_core = 'auto'


_SHOULD_USE_CUDNN = {
    '==always': {'always': True, 'auto': False, 'never': False},
    '>=auto':   {'always': True, 'auto': True,  'never': False},
}


_cudnn_version = cuda.cuda.cudnn.getVersion() if cuda.cudnn_enabled else -1


def should_use_cudnn(level, lowest_version=0):
    """Determines if we should use cuDNN.

    This function checks ``chainer.config.use_cudnn``,
    ``chainer.cuda.cudnn_enabled``, and the cuDNN version. Note that
    ``cudnn_enabled`` flag is fixed at loading of :mod:`chainer` module.

    Args:
        level (str): cuDNN use level. It must be either ``'==always'`` or
            ``'>=auto'``. ``'==always'`` indicates that the ``use_cudnn``
            config must be ``'always'`` to use cuDNN.
        lowest_version (int): Required lowest cuDNN version. It must be
            non-negative.

    Returns:
        bool: ``True`` if the caller should use cuDNN.

    """
    if _cudnn_version < lowest_version:
        return False

    if level not in _SHOULD_USE_CUDNN:
        raise ValueError('invalid cuDNN use level: %s '
                         '(must be either of "==always" or ">=auto")' %
                         repr(level))
    flags = _SHOULD_USE_CUDNN[level]

    use_cudnn = config.use_cudnn
    if use_cudnn not in flags:
        raise ValueError('invalid use_cudnn configuration: %s '
                         '(must be either of "always", "auto", or "never")' %
                         repr(use_cudnn))
    return flags[use_cudnn]


_tensor_core_flag = {'always': True, 'auto': None, 'never': False}


def should_use_cudnn_tensor_core(dtype):
    """Determines if Tensor Core should be used.

    Args:
        dtype (numpy.dtype): data type of input tensor.

    Returns:
        bool: ``True`` if Tensor Core should be used.
    """

    use_cudnn_tensor_core = config.use_cudnn_tensor_core
    if use_cudnn_tensor_core not in _tensor_core_flag:
        raise ValueError('invalid use_cudnn_tensor_core configuration: %s '
                         '(must be either of "always", "auto", or "never")' %
                         repr(use_cudnn_tensor_core))
    use_tensor_core = _tensor_core_flag[use_cudnn_tensor_core]
    if use_tensor_core is None:
        use_tensor_core = cuda.cudnn.is_tensor_core_available(dtype)
    return use_tensor_core


def is_debug():
    """Get the debug mode.

    Returns:
        bool: Return ``True`` if Chainer is in debug mode.
    """
    return bool(config.debug)


def set_debug(debug):
    """Set the debug mode.

    .. note::

        This method changes global state. When you use this method on
        multi-threading environment, it may affects other threads.

    Args:
        debug (bool): New debug mode.
    """
    config.debug = debug


class DebugMode(object):
    """Debug mode context.

    This class provides a context manager for debug mode. When entering the
    context, it sets the debug mode to the value of `debug` parameter with
    memorizing its original value. When exiting the context, it sets the debug
    mode back to the original value.

    .. deprecated:: v2.0.0
       DebugMode is deprecated. Use ``using_config('debug', debug)`` instead.

    Args:
        debug (bool): Debug mode used in the context.
    """

    def __init__(self, debug):
        warnings.warn('chainer.DebugMode is deprecated. '
                      'Use chainer.using_config("debug", ...) instead.',
                      DeprecationWarning)
        self._using = using_config('debug', debug)

    def __enter__(self):
        self._using.__enter__()

    def __exit__(self, *args):
        self._using.__exit__(*args)


basic_math.install_variable_arithmetics()
array.get_item.install_variable_get_item()

disable_experimental_feature_warning = False
