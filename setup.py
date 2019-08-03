"""A setuptools based setup module.

See:
https://github.com/FreeTHX/pywakeps4onbt
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from os import path
from io import open
import wakeps4onbt

NAME='pywakeps4onbt'
DESCRIPTION='A Python library to wakeup Ps4 on BlueTooth'
URL='https://github.com/FreeTHX/pywakeps4onbt'
AUTHOR='FreeTHX'
AUTHOR_EMAIL='freethx.dev@gmail.com'
REQUIRED = ['pybluez']

here = path.abspath(path.dirname(__file__))
# Get the long description from the README file
try:
    with open(path.join(here, 'README.md'), encoding='utf-8') as f:
        LONG_DESCRIPTION = f.read()
except FileNotFoundError:
    LONG_DESCRIPTION = DESCRIPTION    

setup(
    name=NAME,
    version=wakeps4onbt.__version__,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url=URL,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license='Apache License 2.0',
    # For a list of valid classifiers, see https://pypi.org/classifiers/
    classifiers=[  
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Home Automation',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    keywords='wake ps4 on bt home assistant',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),  
    install_requires=REQUIRED,
)
