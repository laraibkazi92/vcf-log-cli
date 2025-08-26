uv pip uninstall vcf-log-cli
rm -rf ./dist/
poetry build
uv pip install ./dist/vcf_log_cli-2.0.4-py3-none-any.whl 
