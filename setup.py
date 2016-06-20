from setuptools import setup, find_packages

setup(
        name="orange",
        version="0.2",
        packages = find_packages(),
        install_requires = ['boto3', 'ansible', 'requests','google-api-python-client']
)
