from setuptools import find_packages, setup

setup(
    name="volunteer-signup",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    package_data={
        "volunteer_signup": ["templates/*.html", "static/*"],
    },
    python_requires=">=3.12",
)