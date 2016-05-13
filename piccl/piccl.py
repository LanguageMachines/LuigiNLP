#!/usr/bin/env python3

import luigi
import logging

log = logging.getLogger('mainlog')
log.level=logging.INFO

def main():
    log.info("Starting PICCL")
    luigi.run(local_scheduler=True)


if __name__ == '__main__':
    main()
