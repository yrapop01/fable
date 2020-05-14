from setuptools import setup
import os

VERSION = '1.0'
VERS = VERSION.replace('.', '')

setup(
    name = 'fable',
    packages = ['fable'],
    version = VERSION,
    license = 'MIT',
    description = 'Fable: Tex Editor',
    author = 'Yuri Rapoport',
    author_email = 'yuri.rapoport@gmail.com',
    url = 'https://github.com/yrapop01/fable',
    download_url = f'https://github.com/yrapop01/fable/archive/v_{VERS}.tar.gz',
    keywords = ['TEX', 'NOTEBOOK', 'LITERATE'],
    install_requires = ['psutil'],
    classifiers = [
      'Development Status :: 3 - Alpha',      # "3 - Alpha", "4 - Beta" or "5 - Production/Stable"
      'Intended Audience :: Developers', 
      'Topic :: Software Development :: Build Tools',
      'License :: OSI Approved :: MIT License',
      'Programming Language :: Python :: 3',
    ]
)
