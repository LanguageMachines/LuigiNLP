#! /usr/bin/env python3
# -*- coding: utf8 -*-


import os
import sys
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name = "LuigiNLP",
    version = "0.1", #edit version in __init__.py as well!
    author = "Maarten van Gompel",
    author_email = "proycon@anaproy.nl",
    description = ("LuigiNLP - Pipeline for Natural Language Processing"),
    license = "GPL",
    keywords = "nlp computational_linguistics",
    url = "https://github.com/LanguageMachines/LuigiNLP",
    packages=['luiginlp','luiginlp.modules'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 1 - Alpha",
        "Topic :: Text Processing :: Linguistic",
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    zip_safe=False,
    #include_package_data=True,
    #package_data = {'': ['*.wsgi','*.js','*.xsl','*.gif','*.png','*.xml','*.html','*.jpg','*.svg','*.rng'] },
    install_requires=['lxml >= 2.2','sciluigi','natsort'],
    entry_points = {    'console_scripts': [
            'luiginlp = luiginlp.luiginlp:main',
    ]
    }
)
