from setuptools import setup, find_packages

setup(
    name='woww',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        # Add any required dependencies here
        'requests'
    ],
    author='Your Name',
    description='Wave and ocean weather wrapper (WOWW)',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)