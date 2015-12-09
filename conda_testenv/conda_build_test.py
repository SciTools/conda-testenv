"""
This module represents code forked from
https://github.com/conda/conda-build/blob/master/conda_build/build.py
to modularise the test creation and running of installed distributions.

The intention is for this factorisation to make it back to conda-build
in the future.

(c) 2012 Continuum Analytics, Inc. / http://continuum.io

"""
from os.path import join
import subprocess
import sys

import conda_build.build
from conda_build.create_test import (create_files, create_shell_files,
                                     create_py_files, create_pl_files)


def create_test_files(m, tmp_dir):
    create_files(tmp_dir, m)
    # Make Perl or Python-specific test files
    if m.name().startswith('perl-'):
        pl_files = create_pl_files(tmp_dir, m)
        py_files = False
    else:
        py_files = create_py_files(tmp_dir, m)
        pl_files = False
    shell_files = create_shell_files(tmp_dir, m)

    return py_files, pl_files, shell_files


def run_tests(m, env, tmp_dir, py_files, pl_files, shell_files):
    if py_files:
        try:
            subprocess.check_call(['python', '-s',
                                   join(tmp_dir, 'run_test.py')],
                                  env=env, cwd=tmp_dir)
        except subprocess.CalledProcessError:
            conda_build.build.tests_failed(m)

    if pl_files:
        try:
            subprocess.check_call(['perl',
                                   join(tmp_dir, 'run_test.pl')],
                                  env=env, cwd=tmp_dir)
        except subprocess.CalledProcessError:
            conda_build.build.tests_failed(m)

    if shell_files:
        if sys.platform == 'win32':
            test_file = join(tmp_dir, 'run_test.bat')
            cmd = [os.environ['COMSPEC'], '/c', 'call', test_file]
            try:
                subprocess.check_call(cmd, env=env, cwd=tmp_dir)
            except subprocess.CalledProcessError:
                conda_build.build.tests_failed(m)
        else:
            test_file = join(tmp_dir, 'run_test.sh')
            # TODO: Run the test/commands here instead of in run_test.py
            cmd = ['/bin/bash', '-x', '-e', test_file]
            try:
                subprocess.check_call(cmd, env=env, cwd=tmp_dir)
            except subprocess.CalledProcessError:
                conda_build.build.tests_failed(m)
