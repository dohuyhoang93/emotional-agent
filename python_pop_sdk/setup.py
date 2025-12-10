from setuptools import setup, find_packages

setup(
    name="pop-sdk",
    version="0.1.0",
    description="Process-Oriented Programming (POP) SDK for Python",
    long_description=open("README.md", encoding="utf-8").read() if open("README.md", encoding="utf-8") else "",
    long_description_content_type="text/markdown",
    author="Do Huy Hoang",
    author_email="dohuyhoangvn93@gmail.com",
    url="https://github.com/dohuyhoang93/pop-sdk",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    python_requires=">=3.8",
)
