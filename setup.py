from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="opentypesvg",
    use_scm_version={'write_to': 'lib/opentypesvg/__version__.py'},
    setup_requires=["setuptools_scm"],
    author="Miguel Sousa",
    author_email="msousa@adobe.com",
    description="Tools for making OpenType-SVG fonts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/adobe-type-tools/opentype-svg",
    license="MIT",
    platforms=["Any"],
    package_dir={'': 'lib'},
    packages=['opentypesvg'],
    python_requires='>=3.6',
    install_requires=['fontTools[woff]>=3.1.0'],
    entry_points={
        'console_scripts': [
            "addsvg = opentypesvg.addsvg:main",
            "dumpsvg = opentypesvg.dumpsvg:main",
            "fonts2svg = opentypesvg.fonts2svg:main",
        ]
    },
)
