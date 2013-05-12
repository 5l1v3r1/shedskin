'''
*** SHED SKIN Python-to-C++ Compiler ***
Copyright 2005-2011 Mark Dufour; License GNU GPL version 3 (See LICENSE)

'''
import getopt
import os.path
import struct
import sys
import time
import traceback

from annotate import annotate
from config import newgx, setgx, getgx
from cpp import generate_code
from error import print_errors
from infer import analyze


def usage():
    print """Usage: shedskin [OPTION]... FILE

 -a --ann               Output annotated source code (.ss.py)
 -b --nobounds          Disable bounds checking
 -e --extmod            Generate extension module
 -f --flags             Provide alternate Makefile flags
 -g --nogcwarns         Disable runtime GC warnings
 -l --long              Use long long ("64-bit") integers
 -m --makefile          Specify alternate Makefile name
 -n --silent            Silent mode, only show warnings
 -o --noassert          Disable assert statements
 -r --random            Use fast random number generator (rand())
 -s --strhash           Use fast string hashing algorithm (murmur)
 -w --nowrap            Disable wrap-around checking
 -x --traceback         Print traceback for uncaught exceptions
 -L --lib               Add a library directory
"""
# -p --pypy              Make extension module PyPy-compatible
# -v --msvc              Output MSVC-style Makefile
    sys.exit(1)


def start():
    setgx(newgx())

    # --- command-line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vbchef:wad:m:rolspxngL:', ['help', 'extmod', 'nobounds', 'nowrap', 'flags=', 'debug=', 'makefile=', 'random', 'noassert', 'long', 'msvc', 'ann', 'strhash', 'pypy', 'traceback', 'silent', 'nogcwarns', 'lib'])
    except getopt.GetoptError:
        usage()

    for o, a in opts:
        if o in ['-h', '--help']:
            usage()
        if o in ['-b', '--nobounds']:
            getgx().bounds_checking = False
        if o in ['-e', '--extmod']:
            getgx().extension_module = True
        if o in ['-a', '--ann']:
            getgx().annotation = True
        if o in ['-d', '--debug']:
            getgx().debug_level = int(a)
        if o in ['-l', '--long']:
            getgx().longlong = True
        if o in ['-g', '--nogcwarns']:
            getgx().gcwarns = False
        if o in ['-w', '--nowrap']:
            getgx().wrap_around_check = False
        if o in ['-r', '--random']:
            getgx().fast_random = True
        if o in ['-o', '--noassert']:
            getgx().assertions = False
        if o in ['-p', '--pypy']:
            getgx().pypy = True
        if o in ['-m', '--makefile']:
            getgx().makefile_name = a
        if o in ['-n', '--silent']:
            getgx().silent = True
        if o in ['-s', '--strhash']:
            getgx().fast_hash = True
        if o in ['-v', '--msvc']:
            getgx().msvc = True
        if o in ['-x', '--traceback']:
            getgx().backtrace = True
        if o in ['-L', '--lib']:
            getgx().libdirs = [a] + getgx().libdirs
        if o in ['-f', '--flags']:
            if not os.path.isfile(a):
                print "*ERROR* no such file: '%s'" % a
                sys.exit(1)
            getgx().flags = a

    if not getgx().silent:
        print '*** SHED SKIN Python-to-C++ Compiler 0.9.3 ***'
        print 'Copyright 2005-2011 Mark Dufour; License GNU GPL version 3 (See LICENSE)'
        print

    # --- some checks
    major, minor = sys.version_info[:2]
    if (major, minor) not in [(2, 4), (2, 5), (2, 6), (2, 7)]:
        print '*ERROR* Shed Skin is not compatible with this version of Python'
        sys.exit(1)
    if sys.platform == 'win32' and os.path.isdir('c:/mingw'):
        print '*ERROR* please rename or remove c:/mingw, as it conflicts with Shed Skin'
        sys.exit()
    if sys.platform == 'win32' and struct.calcsize('P') == 8 and getgx().extension_module:
        print '*WARNING* 64-bit python may not come with necessary file to build extension module'

    # --- argument
    if len(args) != 1:
        usage()
    name = args[0]
    if not name.endswith('.py'):
        name += '.py'
    if not os.path.isfile(name):
        print "*ERROR* no such file: '%s'" % name
        sys.exit(1)
    main_module_name = os.path.splitext(name)[0]

    # --- analyze & annotate
    t0 = time.time()
    analyze(main_module_name)
    annotate()
    generate_code()
    print_errors()
    if not getgx().silent:
        print '[elapsed time: %.2f seconds]' % (time.time() - t0)


def main():
    sys.setrecursionlimit(100000)
    try:
        start()
    except KeyboardInterrupt, e:
        if getgx().debug_level > 0:
            print traceback.format_exc(e)
        sys.exit(1)


if __name__ == '__main__':
    main()
