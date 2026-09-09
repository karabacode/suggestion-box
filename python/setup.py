from setuptools import find_packages, setup


setup(
    name="Suggestions Box",
    version="0.1.0",
    description="FastAPI Gmail connector for suggestion box",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.115.12",
        "google-api-python-client==2.169.0",
        "google-auth-oauthlib==1.2.2",
        "uvicorn[standard]==0.34.2",
    ],
)
