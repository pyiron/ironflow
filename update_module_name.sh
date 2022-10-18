#!/bin/bash

module_name="pyiron_IntendedModuleName"
rst_delimit="========================="   # This should be as many '=' as the name length.

for file in binder/postBuild tests/test_tests.py .coveragerc .gitattributes MANIFEST.in setup.cfg setup.py .github/ISSUE_TEMPLATE/*.md docs/environment.yml binder/environment.yml docs/conf.py notebooks/version.ipynb; do
  sed -i "s/pyiron_module/${module_name}/g" ${file}
done

file=docs/index.rst
sed -i "s/pyiron_module/${module_name}/g" ${file}
sed -i "s/=============/${rst_delimit}/g" ${file}

mv pyiron_module ${module_name}

python -m versioneer setup

rm update_module_name.sh
