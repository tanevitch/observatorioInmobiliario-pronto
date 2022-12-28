clean:
	rm data/clean_data.csv data/positivos.csv data/uris_duplicados.csv

test:
	python3.10 1_remove_excess.py && python3.10 2_link_uris.py && python3.10 3_divide_uris.py
