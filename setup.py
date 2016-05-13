#! /usr/bin/env python3
# -*- coding: utf8 -*-


import os
import sys
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name = "PICCL",
    version = "0.1", #edit version in __init__.py as well!
    author = "Maarten van Gompel",
    author_email = "proycon@anaproy.nl",
    description = ("PICCL - Pipeline for Natural Language Processing - Proof of Concept"),
    license = "GPL",
    keywords = "nlp computational_linguistics",
    url = "https://github.com/LanguageMachines/piccl_proofofconcept",
    packages=['piccl','piccl.workflows','piccl.modules'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 1 -Alpha",
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
    install_requires=['lxml >= 2.2','sciluigi'],
    entry_points = {    'console_scripts': [
            'piccl = piccl.piccl:main',
    ]
    }
)
