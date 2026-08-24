
compile-poltest:
	g++ -O2 pol_test.cpp -o pol_test.out

compile-all: compile-poltest

run-poltest:
	./pol_test.out > ptest.txt
	python pol_test.py < ptest.txt

poltest: compile-poltest run-poltest

clean-poltest:
	rm pol_test.out

clean-all: clean-poltest