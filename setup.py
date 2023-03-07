from setuptools import setup

setup(
    name="intersubs",
    version="0.0.1",
    description="Interactive subtitles for mpv",
    author="Abdo",
    author_email="abd.nh25@gmail.com",
    url="https://github.com/abdnh/intersubs",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=["intersubs"],
    install_requires=[
        "pywin32; sys.platform == 'win32'",
        "mouse==0.7.1"
    ],
    extras_require={
        "qt5": ["pyqt5", "PyQtWebEngine"],
        "qt6": ["PyQt6", "PyQt6-WebEngine"],
    },
)
