import os
import shutil
import subprocess
import sys
import tempfile
import unittest


class Test_cli(unittest.TestCase):
    def setUp(self):
        conda = os.path.join(os.path.dirname(sys.executable), 'conda')
        self.environ = os.environ.copy()
        self.tmpdir = tempfile.mkdtemp('conda_setup')

        condarc = os.path.join(self.tmpdir, 'condarc')
        self.environ['CONDARC'] = condarc
        with open(condarc, 'w') as fh:
            fh.write('add_pip_as_python_dependency: false\n')
            fh.write('conda-build:\n')
            fh.write('    root-dir: {}'.format(os.path.join(self.tmpdir,
                                                            'build-root')))

        recipes_location = os.path.join(os.path.dirname(__file__),
                                        'test_recipes')
        build_environ = self.environ.copy()
        build_environ['CONDA_NPY'] = '110'
        subprocess.check_call([conda, 'build',
                               os.path.join(recipes_location, 'a'),
                               os.path.join(recipes_location, 'b'),
                               os.path.join(recipes_location, 'c'),
                               ],
                              env=build_environ)

        self.test_prefix = os.path.join(self.tmpdir, 'test_prefix')
        cmd = [conda, 'create', '-p', self.test_prefix, 'a', 'b',
               'c', '--use-local', '--yes']
        subprocess.check_call(cmd, env=self.environ)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test(self):
        cmd = ['conda', 'testenv', '-p', self.test_prefix]
        self.assertNotIn('CONDA_NPY', self.environ)
        output = subprocess.check_output(cmd, env=self.environ)
        output = output.decode('ascii')
        self.assertIn('Success recipe a', output)
        self.assertIn('Success recipe b', output)
        self.assertIn('hello from b', output)
        self.assertIn('Success recipe c', output)
        self.assertIn('hello from c', output)
