run:
	./exec.out > input.txt
	python deprecated_stuff/g_viz.py < input.txt
compile:
	g++ -O2 output_graph.cpp -o exec.out
clean:
	rm exec.out
	rm input.txt
test: compile run clean