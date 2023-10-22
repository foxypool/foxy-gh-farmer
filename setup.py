from setuptools import find_packages, setup

setup(
    name='foxy-gh-farmer',
    version='1.2.2',
    url='https://foxypool.io',
    license='GPLv3',
    author='Felix Brucker',
    author_email='contact@foxypool.io',
    description='A simplified Gigahorse farmer for the Chia blockchain using the Foxy Gigahorse Node.',
    install_requires=[
        "aiohttp==3.8.4",
        "aioudp==0.1.1",
        "chia-blockchain==1.8.3rc1",
        "click==8.1.3",
        "humanize==4.8.0",
        "pyparsing==3.1.1",
        "PyYAML==6.0.0",
        "yaspin==3.0.1",
    ],
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
