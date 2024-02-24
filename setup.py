import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aims-convert",
    version="1.2",
    author="Jon Hurst",
    author_email="jon.a@hursts.org.uk",
    description="Extract information from AIMS detailed roster",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    url="https://github.com/JonHurst/aims-convert",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Programming Language :: Python :: 3",
        ("License :: OSI Approved :: "
         "GNU General Public License v3 or later (GPLv3+)"),
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.11',
    install_requires=[
        "requests",
        "nightflight",
    ],
    package_data={
    },
    entry_points={
        "console_scripts": ["aims = aims.cli:main"],
        "gui_scripts" : ["aimsgui = aims.gui:main"]
    },
)
