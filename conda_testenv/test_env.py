from __future__ import print_function

from contextlib import contextmanager
import os
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
    List the sources of all the packages installed in the given environment.

    """
    installed = install.linked(prefix)
    sources = []
    for dist in conda.cli.main_list.get_packages(installed, None):
        info = install.is_linked(prefix, dist)
        sources.append(info['link']['source'])
    return sources


def recipe_exists(source):
    """
    Find the recipe in a source if it exists.

    """
    meta_dir = os.path.join(source, 'info', 'recipe')
    if not os.path.isdir(meta_dir):
        return False
    return meta_dir


@contextmanager
def switch_out_meta_for_orig(recipe_dir):
    """
    Use the original meta.yaml.orig rather than meta.yaml for the lifetime of
    this context manager.

    """
    meta = os.path.join(recipe_dir, 'meta.yaml')
    meta_orig = os.path.join(recipe_dir, 'meta.yaml.orig')
    meta_tmp = os.path.join(recipe_dir, 'meta.yaml.tmp')

    if not os.path.exists(meta_orig):
        yield
    else:
        shutil.move(meta, meta_tmp)
        shutil.move(meta_orig, meta)
        yield
        shutil.move(meta, meta_orig)
        shutil.move(meta_tmp, meta)


def run_pkg_tests(m, env_prefix):
    """
    Run the tests defined in the recipe of a package in the given
    environment.

    """
    tmpdir = tempfile.mkdtemp()
    test_files = conda_build_test.create_test_files(m, tmpdir)
    py_files, pl_files, shell_files = test_files
    if not (py_files or pl_files or shell_files):
        return
    env = os.environ
    env = prepend_bin_path(env, env_prefix, prepend_prefix=True)
    conda_build_test.run_tests(m, env, tmpdir, py_files, pl_files, shell_files)
    shutil.rmtree(tmpdir)


def run_env_tests(env_prefix):
    """
    Run all the tests defined in the recipe of all packages in the given
    environment.

    """
    config.CONDA_NPY = 00
    sources = list_package_sources(env_prefix)
    for source in sources:
        recipe_path = recipe_exists(source)
        if recipe_path:
            with switch_out_meta_for_orig(recipe_path):
                m = conda_build.metadata.MetaData(recipe_path)
                run_pkg_tests(m, env_prefix)
    print('All tests are finished.')
