
best(S, P, O, Valuator, Impact) :-
	% do iterative deepening until we find one good enough
	between(1,10,Step),
	MinQ is Step / 10,
	rule(S,P,O,1.0,MinQ,Valuator,Impact).

given(a,b,c).
given(a,b,d).
given(a,b,e).
given(b,b,c).

rule(S,P,O,_,_,_,given) :-
	given(S,P,O).

% memoize stuff? asserting it to the rdf triple store, maybe,
% with a graph showing its weight....

% one particular rule, ....
rule(S,P,O,QIn,MinQ,Valuator,rule187(X)) :-
	%%%MyImpact = [performance(0.8), presentation(0.25)],
	%%%call(Valuator, MyImpact, MyQuality),
	%   probably, we should just emit different rules
	%   for different valuators...   hardcode into the
	%   rule what its MyQuality is.
	QOut is QIn * 0.75, % * MyQuality,
	format('rule187, ~q~n', [[QIn,MyQuality,QOut,MinQ]]),
	QOut > MinQ,
	% body of rule, using rule(_,_,_,QOut,MinQ,Valuator)
	rule(S,P,c,QOut,MinQ,Valuator,X),
	O=x.

rule(S,P,O,QIn,MinQ,Valuator,rule199(X)) :-
	QOut is QIn * 0.65,
	format('rule199, ~q~n', [[QIn,MyQuality,QOut,MinQ]]),
	QOut > MinQ,
	% body of rule, using rule(_,_,_,QOut,MinQ,Valuator)
	rule(S,P,x,QOut,MinQ,Valuator,X),
	O=c.

impact(ImpactList, Feature, Quality) :-
	Term =.. [Feature, Arg],
	(  member(Term, ImpactList)
	-> Quality = Arg
	;  Quality = 1.0
	).


% what is the quality multiplier, on an ENGINE, if we apply this rule?
engine(Impact, Quality) :-
	impact(Impact, soundness, S),         WS = 0.9,
	impact(Impact, completeness, C),      WC = 0.5,
	impact(Impact, performance, Perf),    WPerf = 0.2,
	impact(Impact, presentation, Pres),   WPres = 0.05,
	% weighted geometric mean, which I think is the right approach,
	% but I'm not very good at statistics....
	% http://en.wikipedia.org/wiki/Weighted_geometric_mean
	Quality is exp( (WS*log(S)+WC*log(C)+WPerf*log(Perf)+WPres*log(Pres)) /
		      (WS + WC + WPerf + WPres ) )
	.

editor(Impact, Quality) :-
	impact(Impact, soundness, S),         WS = 0.8,
	impact(Impact, completeness, C),      WC = 0.8,
	impact(Impact, performance, Perf),    WPerf = 0.8,
	impact(Impact, presentation, Pres),   WPres = 0.9,
	% weighted geometric mean, which I think is the right approach,
	% but I'm not very good at statistics....
	% http://en.wikipedia.org/wiki/Weighted_geometric_mean
	Quality is exp( (WS*log(S)+WC*log(C)+WPerf*log(Perf)+WPres*log(Pres)) /
		      (WS + WC + WPerf + WPres ) )
	.