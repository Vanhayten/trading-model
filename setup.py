from setuptools import setup, find_packages

setup(
    name='trading_model',
    version='0.1',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'click==8.1.7',
        'MetaTrader5==5.0.4424',
        'numpy>=1.26.4',
        'pandas==2.2.0',
        'pydantic==2.5.3',
        'requests==2.31.0',
        'python-dotenv==1.0.0',
        'typer>=0.12.3',
    ],
    python_requires='>=3.9,<3.13',
)