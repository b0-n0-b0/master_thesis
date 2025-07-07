# master_thesis
In order to use this tool:
```
$ docker build -t master_thesis .
$ docker run -v /your_test_folder:/inputs/ master_thesis rule_file.rule /inputs/module_to_analyze.wasm
```
