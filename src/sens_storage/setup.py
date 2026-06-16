from setuptools import find_packages, setup

package_name = "sens_storage"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Sens Engineering",
    maintainer_email="engineering@sens.local",
    description="Storage and engineering dependency graph nodes for the Sens platform.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "storage_node = sens_storage.storage_node:main",
        ],
    },
)
