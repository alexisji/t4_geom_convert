'''.. _pytest: https://docs.pytest.org/en/latest

`pytest`_ configuration file.
'''
import pathlib
import subprocess as sub

import pytest

# pylint: disable=redefined-outer-name

# pylint: disable=redefined-outer-name


def pytest_addoption(parser):
    '''Add the ``--oracle-path`` and ``--mcnp-path`` options to `pytest`.'''
    parser.addoption('--oracle-path', action='store',
                     help='path to the oracle executable', default=None,
                     type=pathlib.Path)
    parser.addoption('--mcnp-path', action='store',
                     help='path to the MCNP executable', default=None,
                     type=pathlib.Path)
    parser.addoption('--extra-mcnp-input', action='append',
                     help='Add an extra MCNP input file to test conversion',
                     default=[],
                     type=pathlib.Path)


def pytest_collection_modifyitems(config, items):
    '''Handle CLI options to pytest.'''
    a_mcnp_path = config.getoption('--mcnp-path')
    a_or_path = config.getoption('--oracle-path')
    if not (a_mcnp_path and a_mcnp_path.exists()
            and a_or_path and a_or_path.exists()):
        skip_or = pytest.mark.skip(reason='needs --mcnp-path and '
                                   '--oracle-path options to run')
        for item in items:
            if 'oracle' in item.keywords:
                item.add_marker(skip_or)


def pytest_generate_tests(metafunc):
    '''Generate tests for the --extra-mcnp-input option'''
    # This is called for every test. Only get/set command line arguments
    # if the argument is specified in the list of test "fixturenames".
    extra_inputs = metafunc.config.option.extra_mcnp_input
    if 'extra_input' in metafunc.fixturenames:
        paths = [path.resolve() for path in extra_inputs]
        ids = [path.name for path in paths]
        metafunc.parametrize('extra_input', paths, ids=ids)


##############
#  fixtures  #
##############


@pytest.fixture
def datadir(tmp_path, request):
    '''Fixture responsible for searching a folder called 'data' in the same
    directory as the test module and, if available, moving all contents to a
    temporary directory so tests can use them freely.
    '''
    filename = request.fspath
    test_dir = filename.dirpath('data')

    if test_dir.check():
        test_dir.copy(tmp_path)

    return tmp_path


@pytest.fixture
def mcnp_path(request):
    '''Fixture yielding the path to the MCNP executable specified on the
    command line.'''
    return request.config.getoption('--mcnp-path')


@pytest.fixture
def oracle_path(request):
    '''Fixture yielding the path to the oracle executable specified on the
    command line.'''
    return request.config.getoption('--oracle-path')


def foreach_data(*args, **kwargs):
    '''Decorator that parametrizes a test function over files in the data
    directory for the current tests.

    Assume that the following snippet resides in
    :file:`tests/submod/test_submod.py`::

        @foreach_data('datafile')
        def test_something(datafile):
            pass

    When `pytest` imports :file:`test_submod.py`, it will parametrize
    the `datafile` argument to :func:`!test_something` over all the files
    present in :file:`tests/submod/data/`.

    If you wish to filter away some of the files, you can use the alternative
    syntax::

        @foreach_data(datafile=lambda path: str(path).endswith('.txt'))
        def test_something(datafile):
            pass

    Here the argument to the `datafile` keyword argument is a predicate that
    must return `True` if `path` is to be parametrized over, and `False`
    otherwise. Note that the `path` argument to the lambda is a
    :class:`py._path.local.LocalPath` object.  In this example, `pytest` will
    parametrize :func:`!test_something` only over files whose name ends in
    ``'.txt'``.
    '''

    if args:
        if len(args) != 1:
            raise ValueError('Only one positional argument allowed to '
                             '@foreach_data')
        if kwargs:
            raise ValueError('No kwargs allowed with a positional '
                             'argument to @foreach_data')
        fix_name = args[0]
        def fil(name):
            return True
    else:
        if len(kwargs) != 1:
            raise ValueError('Only one kwarg allowed in @foreach_data')
        fix_name, fil = next(iter(kwargs.items()))

    def _decorator(wrapped, fil=fil):
        from inspect import getfile
        module_dir = pathlib.Path(getfile(wrapped))  # pylint: disable=E1101
        test_dir = module_dir.parent / 'data'
        datafiles = [path for path in test_dir.iterdir()
                     if path.is_file() and fil(path)]
        ids = [str(path.name) for path in datafiles]
        return pytest.mark.parametrize(fix_name, datafiles, ids=ids)(wrapped)
    return _decorator


class MCNPRunner:  # pylint: disable=too-few-public-methods
    '''A helper class to run MCNP on a given input file.'''

    def __init__(self, path, work_path):
        '''Create an instance of :class:`MCNPRunner`.

        :param path: path to the MCNP executable
        :type path: str or path-like object
        :param work_path: path to the working directory
        :type work_path: str or path-like object
        '''
        self.path = path
        self.work_path = work_path

    def run(self, input_file):
        '''Run MCNP on the given input file.

        :param str input_file: absolute path to the input file
        :returns: the path to the generated PTRAC file
        :rtype: str or path-like object
        '''
        run_name = 'run_' + input_file.name
        cli = [str(self.path),
               'inp={}'.format(input_file),
               'name={}'.format(run_name)]
        sub.check_call(cli, cwd=str(self.work_path))
        return self.work_path / (run_name + 'p')


@pytest.fixture
def mcnp(mcnp_path, tmp_path):
    '''Return an instance of the :class:`MCNPRunner` class.'''
    return MCNPRunner(mcnp_path, tmp_path)


class OracleRunner:  # pylint: disable=too-few-public-methods
    '''A helper class to run the test oracle.'''

    def __init__(self, path, work_path):
        '''Create an instance of :class:`OracleRunner`.

        :param path: path to the MCNP executable
        :type path: str or path-like object
        :param work_path: path to the working directory
        :type work_path: str or path-like object
        '''
        self.path = path
        self.work_path = work_path

    def run(self, t4_o, mcnp_i, mcnp_ptrac):
        '''Run the test oracle on the given files.

        :param str t4_o: absolute path to the TRIPOLI-4 file to test
        :param str mcnp_i: absolute path to the MCNP input file
        :param str mcnp_ptrac: absolute path to the MCNP PTRAC file
        :returns: the number of failed points in the comparison
        '''
        cli = [str(self.path), str(t4_o), str(mcnp_i), str(mcnp_ptrac)]
        sub.check_call(cli, cwd=str(self.work_path))
        failed_path = self.work_path / (t4_o.stem + '.failedpoints.dat')
        with failed_path.open() as failed_path_file:
            return len(failed_path_file.readlines())


@pytest.fixture
def oracle(oracle_path, tmp_path):
    '''Return an instance of the :class:`OracleRunner` class.'''
    return OracleRunner(oracle_path, tmp_path)
