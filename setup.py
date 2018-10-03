from pip.req import parse_requirements
from setuptools import find_packages, setup

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements('requirements.txt', session=False)
testing_reqs = parse_requirements('test_requirements.txt', session=False)

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
reqs = [str(ir.req) for ir in install_reqs]
test_reqs = [str(ir.req) for ir in testing_reqs]


setup(
    name='dcumiddleware',
    version='1.0',
    description='middleware for processing API requests',
    author='DCU',
    author_email='dcueng@godaddy.com',
    url='https://github.secureserver.net/ITSecurity/DCUMiddleware',
    # packages=packages,
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=reqs,
    tests_require=test_reqs,
    test_suite="nose.collector")
