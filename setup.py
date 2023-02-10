from setuptools import find_namespace_packages, setup


def setup_package():
    with open('requirements.txt') as file:
        requirements = [
            package.replace('\n', '')
            for package in file.readlines()
        ]
            

    with open('LISENCE', 'r') as file:
        lisence = file.read()

    with open('README.md', 'r') as file:
        readme = file.read()

    setup(
        name='surena',
        version='0.0.1',
        packages=find_namespace_packages('src'),
        author='Mohammad Norouzzadegan',
        author_email='Norouzzadegan@gmail.com',
        description=readme,
        package_dir={'': 'src'},
        install_requires=requirements,
        url='https://github.com/norouzzadegan/surena.git',
        license_files=lisence,
        python_requires='>=3.7,<4',
        entry_points={
            'console_scripts': ['surena=surena.cli:cli'],
        }
    )


if __name__ == '__main__':
    setup_package()
