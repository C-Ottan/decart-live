from setuptools import setup, find_packages

setup(
    name="vidu-sdk",
    version="1.0.0",
    description="Python SDK for Reactor's real-time Vidu S2-Editing model",
    author="Reactor Community",
    packages=find_packages(),
    install_requires=[
        "reactor-sdk>=1.8.0",
        "opencv-python>=4.8.0",
        "pydantic>=2.0.0",
        "numpy>=1.24.0",
        "pillow>=10.0.0",
    ],
    python_requires=">=3.10",
)
