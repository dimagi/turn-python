import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="turn-python",
    version="1.0.0",
    author="Dimagi, inc",
    author_email="dev@dimagi.com",
    description="A python package for the Turn.io WhatsApp API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dimagi/turn-python/",
    packages=setuptools.find_packages(exclude=("tests",)),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
