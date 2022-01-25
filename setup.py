from setuptools import setup

setup(
    name='higlassUp',
    version='0.1',
    py_modules=['higlassUp'],
    data_files=[("./", ["hg19.chrom.sizes", "hg38.chrom.sizes", "mm9.chrom.sizes", "sacCer3.chrom.sizes"])],
    install_requires=[
        'Click',
        'clodius'
    ],
    entry_points='''
        [console_scripts]
        higlassUp=higlassUp:main
    ''',
)