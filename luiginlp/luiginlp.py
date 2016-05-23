#!/usr/bin/env python3

import luigi
import logging
from luiginlp.engine import Parallel, run

log = logging.getLogger('mainlog')
log.level=logging.INFO


def main():
    log.info("Starting LuigiNLP")
    run()

if __name__ == '__main__':
    main()
