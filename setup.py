from sys import platform

from setuptools import find_packages, setup

dependencies = [
    "aiohttp>=3.8.5",
    "aioudp==0.1.1",
    "blspy>=2.0.2",
    "chia-blockchain==2.1.3",
    "click>=8.1.3",
    "colorlog>=6.7.0",
    "humanize==4.8.0",
    "pyparsing==3.1.1",
    "PyYAML>=6.0.1",
    "sentry-sdk==1.33.1",
    "yaspin==3.0.1",
]
if platform == "win32" or platform == "cygwin":
    dependencies.append("pywin32>=306")

setup(
    name='foxy-gh-farmer',
    version='1.8.0',
    url='https://foxypool.io',
    license='GPLv3',
    author='Felix Brucker',
    author_email='contact@foxypool.io',
    description='A simplified Gigahorse farmer for the Chia blockchain using the Foxy Gigahorse Farming Gateway.',
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=dependencies,
    packages=find_packages(include=["foxy_gh_farmer", "foxy_gh_farmer.*"]),
    extras_require=dict(
        dev=[
            "pyinstaller>=5.12",
        ]
    ),
    entry_points={
        "console_scripts": [
            "foxy-gh-farmer = foxy_gh_farmer.foxy_gh_farmer_main:main",
        ],
    },
)
