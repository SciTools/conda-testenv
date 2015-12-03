from setuptools import setup
import versioneer


setup(
      name='conda-testenv',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='Run the tests of all packages installed in a conda environment',
      author='Laura Dreyer',
      author_email='lbdreyer@users.noreply.github.com',
      url='https://github.com/scitools/conda-testenv',
      packages=['conda_testenv'],
      entry_points={
          'console_scripts': [
              'conda-testenv = conda_testenv.cli:main',
          ]
      },
     )

