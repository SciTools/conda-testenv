from contextlib import contextmanager
import os
from os.path import exists, isdir, isfile, islink, join
import shutil
import subprocess
import sys
import tempfile

import conda.cli.main_list
import conda.install as install
import conda_build.build
from conda_build.config import config
import conda_build.metadata
from conda_build.scripts import prepend_bin_path


def list_package_sources(prefix):
    """ 
    List the sources of the packages installed in an environment.
    
    """
    installed = install.linked(prefix)
    sources = []
    for dist in conda.cli.main_list.get_packages(installed, None):
        info = install.is_linked(prefix, dist)
        sources.append(info['link']['source'])
    return sources

def recipe_exist(source):
    """
    Find the recipe in a source if it exists.
    
    """
    meta_dir = join(source, 'info', 'recipe')
    if not isdir(meta_dir):
        return False
    return meta_dir

@contextmanager
def switch_out_meta_for_orig(recipe_dir):
    """
    Use the original meta.yaml.orig rather than meta.yaml for the lifetime of
    this context manager.

    """
    meta = join(recipe_dir, 'meta.yaml')
    meta_orig = join(recipe_dir, 'meta.yaml.orig')
    meta_tmp = join(recipe_dir, 'meta.yaml.tmp')

    if not exists(meta_orig):
        yield
    else:
        shutil.move(meta, meta_tmp)
        shutil.move(meta_orig, meta)
        yield
        shutil.move(meta, meta_orig)
        shutil.move(meta_tmp, meta)

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

def run_pkg_tests(m, env_prefix):
    """
    Run the tests defined in a package's recipe in the given environment.

    """
    tmp_dir = tempfile.mkdtemp()
    config.CONDA_NPY = 19 # get this from environment
    py_files, pl_files, shell_files = conda_build.build.create_test_files(m, tmp_dir)
    if not (py_files, pl_files, shell_files):
        return
    env = os.environ
    env = prepend_bin_path(env, env_prefix, prepend_prefix=True)
    run_tests(m, env, tmp_dir, py_files, pl_files, shell_files)
    shutil.rmtree(tmp_dir)

def run_env_tests(env_prefix):
    """
    Run all tests of the packages in an environment.

    """
    sources = list_package_sources(env_prefix)
    for source in sources:
        recipe_path = recipe_exist(source)
        if recipe_path:
            with switch_out_meta_for_orig(recipe_path):
                m = conda_build.metadata.MetaData(recipe_path)
                run_pkg_tests(m, env_prefix)
