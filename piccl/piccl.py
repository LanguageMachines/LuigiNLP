#!/usr/bin/env python3

import luigi
import logging

log = logging.getLogger('mainlog')
log.basicConfig(level=logging.INFO)


if __name__ == '__main__':
    log.info("Starting PICCL")
    luigi.run(local_scheduler=True)
