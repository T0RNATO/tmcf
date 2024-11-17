from setuptools import setup
setup(
    name = 'tmcf',
    version = '0.1.0',
    packages = ['tmcf'],
    entry_points = {
        'console_scripts': [
            'tmcf = tmcf.main:main'
        ]
    })