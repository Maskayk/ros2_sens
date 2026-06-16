from setuptools import find_packages, setup

package_name = "sens_drivers"

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
    description="Input/output drivers and simulation nodes for the Sens platform.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "sim_plc_node = sens_drivers.sim_plc_node:main",
        ],
    },
)
