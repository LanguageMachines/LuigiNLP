#!/usr/bin/env python3

import luigi
import logging
from luiginlp.engine import Parallel, run
from luiginlp.util import getlog

log = getlog()
log.setLevel(logging.DEBUG)
luigi_logger = logging.getLogger('luigi-interface')
luigi_logger.setLevel(logging.DEBUG)

def main():
    log.info("Starting LuigiNLP")
    run()

if __name__ == '__main__':
    main()
