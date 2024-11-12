
PACKAGE_CONFIG = {
    'numpy': {
        'build_system': 'setuptools',
        'use_sdist': False,
        'test_command': [
            'coverage', 'run', '-m', 'pytest',
            '--cov=numpy',
            '--cov-report=xml:coverage.xml',
            '--cov-report=html:coverage_html',
            '--cov-branch'
        ],
        'additional_env': {'NUMPY_EXPERIMENTAL_DTYPE_API': '1'},
        'dependencies': ['setuptools', 'wheel', 'Cython', 'pybind11'],
        'test_dependencies': ['coverage', 'pytest', 'hypothesis', 'toml', 'pytest-cov']
    },
    'pandas': {
        'build_system': 'setuptools',
        'use_sdist': False,
        'test_command': [
            'coverage', 'run', '-m', 'pytest',
            '--cov=pandas',
            '--cov-report=xml:coverage.xml',
            '--cov-report=html:coverage_html',
            '--cov-branch'
        ],
        'additional_env': {},
        'dependencies': ['setuptools', 'wheel', 'Cython', 'numpy>=2.1.3'],
        'test_dependencies': [
            'coverage', 'pytest', 'hypothesis', 'toml', 'pytest-cov',
            'pytest-xdist', 'psutil', 'python-dateutil>=2.8.2', 'pytz>=2020.1',
            'pytest-forked', 'pyarrow', 'xlrd', 'openpyxl', 'xlwt', 'lxml',
            'html5lib', 'BeautifulSoup4', 'PyYAML', 'mypy', 'black', 'isort',
            'flake8', 'pyodbc', 'fastparquet', 'matplotlib', 'tables',
            'feather-format', 'xarray', 'scipy', 'pandas_datareader', 'pillow',
            'numba', 'fsspec', 's3fs', 'gcsfs', 'pyxlsb', 'blosc',
            'pytest-timeout', 'pytest-asyncio', 'pytest-rerunfailures',
            'pytest-check-links', 'pyreadstat', 'snappy', 'fastavro',
            'psycopg2-binary', 'sqlalchemy', 'greenlet', 'hyperschema',
            'pytest-benchmark', 'hypothesis[django]', 'django', 'requests', 'jinja2'
        ]
    },
    'requests': {
        'build_system': 'setuptools',
        'use_sdist': True,
        'test_command': [
            'coverage', 'run', '-m', 'pytest',
            '--cov=requests',
            '--cov-report=xml:coverage.xml',
            '--cov-report=html:coverage_html',
            '--cov-branch'
        ],
        'additional_env': {},
        'dependencies': ['setuptools', 'wheel'],
        'test_dependencies': ['coverage', 'pytest', 'toml', 'pytest-cov']
    },
    'flask': {
        'build_system': 'setuptools',
        'use_sdist': True,
        'test_command': [
            'coverage', 'run', '-m', 'pytest',
            '--cov=flask',
            '--cov-report=xml:coverage.xml',
            '--cov-report=html:coverage_html',
            '--cov-branch'
        ],
        'additional_env': {},
        'dependencies': ['setuptools', 'wheel'],
        'test_dependencies': ['coverage', 'pytest', 'pytest-cov']
    }
}