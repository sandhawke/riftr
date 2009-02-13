

clean:
	rm -f lextab.py parsetab.py *.pyc parser.out

run_mps: grammar_gen.py mps.bnf
	sed -n '1,/#CUT1/p' < mps_in.py > ,part1
	python grammar_gen.py < mps.bnf > ,part2
	sed -n '/#CUT2/,$$p' < mps_in.py > ,part3
	cat ,part1 ,part2 ,part3 > mps_in_x.py
	python mps_in.py