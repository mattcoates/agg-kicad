"""
compilelib.py

Build a single KiCAD component library from multiple input libraries.

Usage: compilelib.py <lib path> <outfile> [--verify]

With --verify, checks that <outfile> matches the library that would be
generated, exits with 0 if match and 1 otherwise.
"""

from __future__ import print_function

import sys
import os
import fnmatch
import datetime
import subprocess


def git_version(libpath):
    # Handle running inside a git hook where the presence of these environment
    # variables will cause problems
    env = os.environ.copy()
    if 'GIT_DIR' in env:
        del env['GIT_DIR']
    if 'GIT_INDEX_FILE' in env:
        del env['GIT_INDEX_FILE']

    args = ["git", "describe", "--abbrev=8", "--dirty=-dirty", "--always"]
    git = subprocess.Popen(args, cwd=libpath, env=env, stdout=subprocess.PIPE)
    return git.stdout.read().decode().strip()


def writelib(libpath, outpath):
    newlib = compilelib(libpath)
    with open(outpath, "w") as f:
        f.write(newlib)


def checklib(libpath, outpath):
    with open(outpath) as f:
        old = f.read().split("\n")
        new = compilelib(libpath).split("\n")
        # Don't compare the date or git commit strings
        old[5] = old[6] = new[5] = new[6] = None
        return old == new


def compilelib(libpath):
    version = git_version(libpath)
    lines = []
    lines.append("EESchema-LIBRARY Version 2.3\n")
    lines.append("#encoding utf-8\n\n")
    lines.append("#" + "="*78 + "\n")
    lines.append("# Automatically generated by agg-kicad compilelib.py\n")
    lines.append("# on {}\n".format(datetime.datetime.now()))
    lines.append("# using git version {}\n".format(version))
    lines.append("# See github.com/adamgreig/agg-kicad\n")
    lines.append("#" + "="*78 + "\n\n")

    for dirpath, dirnames, files in os.walk(libpath):
        dirnames.sort()
        for f in fnmatch.filter(sorted(files), "*.lib"):
            with open(os.path.join(dirpath, f)) as libf:
                part = libf.readlines()[2:-1]
                if len(part) > 2 and "agg-kicad compilelib.py" not in part[2]:
                    lines.append("".join(part))

    lines.append("# End of library\n")

    return "".join(lines)


def usage():
    print("Usage: {} <lib path> <outfile> [--verify]".format(sys.argv[0]))
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        usage()
    else:
        libpath = sys.argv[1]
        outpath = sys.argv[2]
        if len(sys.argv) == 3:
            writelib(libpath, outpath)
        elif len(sys.argv) == 4 and sys.argv[3] == "--verify":
            if checklib(libpath, outpath):
                print("OK: '{}' is up-to-date with '{}'."
                      .format(outpath, libpath))
                sys.exit(0)
            else:
                print("Error: '{}' is not up-to-date with '{}'."
                      .format(outpath, libpath), file=sys.stderr)
                print("Please run compilelib.py to regenerate.",
                      file=sys.stderr)
                sys.exit(1)
        else:
            usage()
