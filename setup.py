from setuptools import find_packages, setup


setup(
    name="volunteer-signup",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.12",
)