from contextlib import contextmanager
import os
from os.path import exists, isdir, isfile, islink, join
import shutil
import tempfile

import conda.cli.main_list
import conda.install as install
from conda_build.config import config
import conda_build.metadata
from conda_build.scripts import prepend_bin_path

from conda_testenv import conda_build_test


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

def run_pkg_tests(m, env_prefix):
    """
    Run all the tests defined in the recipe of a package in the given
    environment.

    """
    tmp_dir = tempfile.mkdtemp()
    config.CONDA_NPY = 00 # get this from environment # somewhere else!
    py_files, pl_files, shell_files = conda_build_test.create_test_files(m, tmp_dir)
    if not (py_files, pl_files, shell_files):
        return
    env = os.environ
    env = prepend_bin_path(env, env_prefix, prepend_prefix=True)
    conda_build_test.run_tests(m, env, tmp_dir, py_files, pl_files, shell_files)
    shutil.rmtree(tmp_dir)

def run_env_tests(env_prefix):
    """
    Run all the tests of the packages in an environment.

    """
    sources = list_package_sources(env_prefix)
    for source in sources:
        recipe_path = recipe_exist(source)
        if recipe_path:
            with switch_out_meta_for_orig(recipe_path):
                m = conda_build.metadata.MetaData(recipe_path)
                run_pkg_tests(m, env_prefix)
    print('All tests are finished.')
