from __future__ import print_function
import argparse

import conda_testenv.test_env as test_env


def main():
    parser = argparse.ArgumentParser(description='Tool for testing all conda packages in a conda environments')

    parser.add_argument('-p', dest='prefix')
    args = parser.parse_args()

    prefix = args.prefix
    test_env.run_env_tests(prefix)


if __name__ == '__main__':
    main()
