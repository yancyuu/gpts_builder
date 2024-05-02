from setuptools import setup, find_packages

setup(
    name="gpts_builder",
    version="0.1.0",
    author="yancyyu",
    author_email="yancyyu.ok@gmail.com",
    description="A Python library for quickly building applications with large language models.",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'aioredis==2.0.1',
        'anyio==4.3.0',
        'async-timeout==4.0.3',
        'backoff==2.2.1',
        'certifi==2024.2.2',
        'charset-normalizer==3.3.2',
        'exceptiongroup==1.2.1',
        'h11==0.14.0',
        'httpcore==1.0.5',
        'httpx==0.27.0',
        'idna==3.7',
        'redis==5.0.4',
        'regex==2024.4.28',
        'requests==2.31.0',
        'sniffio==1.3.1',
        'tiktoken==0.6.0',
        'typing_extensions==4.11.0',
        'urllib3==2.2.1',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    url="http://github/gpts_builder",  # Optional
    keywords="GPT, large language models, AI, application builder",
    zip_safe=False
)
