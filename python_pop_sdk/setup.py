from setuptools import setup, find_packages

setup(
    name="pop-sdk",
    version="0.2.3",
    description="Process-Oriented Programming (POP) SDK for Python",
    long_description=open("README.md", encoding="utf-8").read() if open("README.md", encoding="utf-8") else "",
    long_description_content_type="text/markdown",
    author="Do Huy Hoang",
    author_email="dohuyhoangvn93@gmail.com",
    url="https://github.com/dohuyhoang93/pop-sdk",
    keywords=["ai", "agent", "pop", "process-oriented", "transactional", "state-management"],
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    entry_points={
        'console_scripts': [
            'pop = pop.cli:main',
        ],
    },
    python_requires=">=3.8",
    project_urls={
        "Source": "https://github.com/dohuyhoang93/pop-sdk",
        "Bug Tracker": "https://github.com/dohuyhoang93/pop-sdk/issues",
    },
)
