import os
import setuptools

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setuptools.setup(
    name="tablechangelogger",
    version="0.0.2",
    author="Volt Lines",
    author_email="tech@voltlines.com",
    description="""A python package which logs each change made to a Django model instance""",
    url="https://github.com/voltlines/django-table-change-logger",
    packages=setuptools.find_packages(),
    license='MIT',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    install_requires=[
        'Django>=1.11',
        'factory-boy==2.11.1',
        'pytest',
        'mock'
    ]
)
