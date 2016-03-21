#!/usr/bin/env python
from distutils.core import setup

from pip.req import parse_requirements

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements('requirements.txt')
test_reqs = parse_requirements('test_requirements.txt')

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
reqs = [str(ir.req) for ir in install_reqs]


setup(name='dcumiddleware',
      version='1.0',
      description='middleware for processing API requests',
      author='DCU',
      author_email='dcueng@godaddy.com',
      url='https://github.secureserver.net/ITSecurity/DCUMiddleware'
      # packages=packages,
      package_dir={'dcumiddleware': 'dcumiddleware'},
      include_package_data=True,
      install_requires=reqs,
      tests_require=test_reqs,
      test_suite="nose.collector"
     )
