import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aims",
    version="0.0.1",
    author="Jon Hurst",
    author_email="jon.a@hursts.org.uk",
    description="Extract information from AIMS detailed roster",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: Console",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
    install_requires=[
        "requests",
    ],
    package_data={
    },
    entry_points={
        "console_scripts": [
            "aims2 = aims.main:main",
        ]
    },
)
