
all: check_yaml build_tlm

check_yaml:
	../yaml_check.py ./tlm_example.yaml

build_tlm:
	../alc.py -iyt ./tlm_example.yaml

clean:
	rm *.anki.import.*
