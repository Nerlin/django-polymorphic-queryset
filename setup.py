import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="django-polymorphic-queryset",
    version="0.2.1",
    author="Artem Yastrebkov",
    author_email="nerlin57@gmail.com",
    description="Polymorphic inheritance for Django QuerySet",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Nerlin/django-polymorphic-queryset",
    packages=setuptools.find_packages(),
    classifiers=(
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 1.9",
        "Framework :: Django :: 1.10",
        "Framework :: Django :: 1.11",
        "Framework :: Django :: 2.0",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Database"
    ),
    install_requires=["Django >= 1.9"]
)