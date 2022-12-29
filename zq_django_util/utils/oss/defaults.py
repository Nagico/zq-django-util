# -*- coding: utf-8 -*-

"""
Global defaults
"""

import loguru

# Default logger
log = loguru.logger


def logger() -> loguru.Logger:
    return log
