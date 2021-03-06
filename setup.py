from setuptools import setup


kwargs = {}

setup(
    use_scm_version={'version_scheme': 'post-release', 'local_scheme': 'dirty-tag'},
    setup_requires=['setuptools >= 40.7.0', 'setuptools_scm >= 1.7.0'],
    **kwargs
)
