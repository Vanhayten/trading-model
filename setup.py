from setuptools import setup, find_packages

setup(
    name='trading_model',
    version='0.1',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'click>=8.1.7,<9.0.0',
        'MetaTrader5>=5.0.37',
        'numpy>=1.21.4,<2.0.0',
        'pandas>=1.3.4,<2.0.0',
        'pydantic>=1.8.2,<2.0.0',
        'requests>=2.26.0,<3.0.0',
        'python-dotenv==1.0.0',
    ],
)
