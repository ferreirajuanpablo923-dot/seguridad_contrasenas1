from setuptools import setup, find_packages

setup(
    name='seguridad_contrasenas',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask',
    ],
    entry_points={
        'console_scripts': [
            'seguridad_contrasenas = app:app'
        ],
    },
)
