from setuptools import setup, find_packages

setup(
    name='data_watchtower',
    version='0.0.1',
    packages=find_packages(exclude=['macros']),
    url='https://github.com/acracker/data_watchtower',
    license='MIT',
    author='acracker',
    author_email='acracker@163.com',
    description='Data quality inspection tool. Identify issues before your CTO detects them!'
)
