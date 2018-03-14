#!/usr/bin/env python3
import sys
assert_statement = "Requires Python{mjr}.{mnr} or greater".format(
    mjr='3',
    mnr='4')
assert sys.version_info >= (3, 4), assert_statement

from groupby import main

if __name__ == '__main__':
    main()
