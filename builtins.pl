
:- ensure_loaded(library(lists)).

run_query(FromFile, ToFile) :-
   ensure_loaded(FromFile),
   open(ToFile, write, Fd),
   forall(
      query(Vars),
      ( 
         forall(
            member(Var, Vars),
            format(Fd, '~q~n', [Var])
         ),
         format(Fd, 'end marker~n', [])
      )
   ),
   close(Fd).

% map data values toward root of datatype tree
promote(data(X,XT), data(X,XT)).
promote(data(X,XT), data(X,YT)) :-
	supertype(Mid, XT),
	promote(data(X,Mid), data(X,YT)).


% direct super datatype relations
% copied from http://www.w3.org/TR/rif-dtb/#Datatypes
supertype(xs_dateTime, xs_dateTimeStamp).
supertype(xs_decimal, xs_integer).
supertype(            xs_integer, xs_long).
supertype(                        xs_long, xs_int).
supertype(                                 xs_int, xs_short).
supertype(                                         xs_short, xs_byte).
supertype(            xs_integer, xs_nonNegativeInteger).
supertype(                        xs_nonNegativeInteger, xs_positiveInteger).
supertype(                           xs_positiveInteger, xs_unsignedLong).
supertype(                             xs_unsignedLong, xs_unsignedInt).
supertype(                               xs_unsignedInt, xs_unsignedShort).
supertype(                                 xs_unsignedShort, xs_unsignedByte).
supertype(            xs_integer, xs_nonPositiveInteger).
supertype(                        xs_nonPositiveInteger, xs_negativeInteger).
supertype(xs_string, xs_normalizedString).
supertype(           xs_normalizedString, xs_token).
supertype(                                xs_token, xs_language).
supertype(                                xs_token, xs_Name).
supertype(                                          xs_Name, xs_NCName).
supertype(                                xs_token, xs_NMTOKEN).


%%
%% data_number(data(LexRep, Datatype), Number)
%%
%%    map back and forth between data/2 terms and prolog numbers.
%%
data_number(D, I) :-
  ground(D), !,
  once(promote(D, data(A, xs_decimal))),
  atom_number(A, I).
data_number(D, I) :-
  ground(I), !,
  atom_number(A, I),
  (  integer(I)
  -> D=data(A,xs_integer)
  ;  D=data(A,xs_decimal)
  ).



% http://www.w3.org/TR/rif-dtb/#pred:literal-not-identical
builtin_literal_not_identical(X, Y) :-
	( promote(X, data(V, T)),
	  promote(Y, data(V, T))
        -> fail
        ;  true
        ).


builtin_is_list([]).
builtin_is_list([_|_]).

builtin_list_contains(List, Item) :-
  memberchk(Item, List).

% my approach to handling functions in prolog. NOT a RIF Builtin
builtin_eval(Result, Expr) :-
  Expr =.. [Functor | Args],
  New =.. [Functor, Result, Args],   % keep args in list, for var-args
  New.

builtin_make_list(Result, Args) :-
  Result = Args.

builtin_count(Result, [List]) :-
  length(List, X),
  atom_number(A, X),
  Result=data(A, xs_integer).   % why xs_integer? how-to-value-space-compare?

% http://www.w3.org/TR/rif-dtb/#func:get
builtin_get(Result, [List, Position]) :-
  data_number(Position, PI),
  builtin_get_i(Result, [List, PI]).

position_adjust(NewPosition, Position, List) :-
  length(List, Len),
  ( Position < 0
  -> NewPosition is Position + Len
  ; NewPosition = Position
  ).

builtin_get_i(Result, [List, Position]) :-
  position_adjust(NewPosition, Position, List),
  nth0(NewPosition, List, Result).

% http://www.w3.org/TR/rif-dtb/#func:sublist_.28adapted_from_fn:subsequence.29
builtin_sublist(Result, [List, Start, Stop]) :-
  !,   % trim the harmless extra choicepoint
  data_number(Start, IStart),
  position_adjust(IStart2, IStart, List),
  data_number(Stop, IStop), 
  position_adjust(IStop2, IStop, List),
  builtin_sublist_i(Result, List, IStart2, IStop2).
builtin_sublist(Result, [List, Start]) :-
  data_number(Start, IStart),
  position_adjust(IStart2, IStart, List),
  length(List, IStop2),
  builtin_sublist_i(Result, List, IStart2, IStop2).

builtin_sublist_i(L1, L2, Start, Stop) :-
  append(Left, Rest, L2),
  length(Left, Start),
  Len is Stop - Start,
  append(L1, _, Rest),
  length(L1, Len), !.

 
% http://www.w3.org/TR/rif-dtb/#func:append
builtin_append(Result, [List|Items]) :-
  append(List, Items, Result).

% http://www.w3.org/TR/rif-dtb/#func:concatenate_.28adapted_from_fn:concatenate.29
builtin_concatenate([], []) :- !.
builtin_concatenate(L, [L]) :- !.
builtin_concatenate(Result, [L|Ls]) :-
   builtin_concatenate(X, Ls),
   append(L, X, Result).

% func:insert-before
builtin_insert_before(Result, [List, Position, NewItem]) :-
   builtin_sublist(A, [List, data('0', xs_int), Position]),
   builtin_sublist(B, [List, Position]),
   append(A, [NewItem|B], Result).

% func:remove
builtin_remove(Result, [List, Position]) :-
   builtin_sublist(A, [List, data('0', xs_int), Position]),
   builtin_sublist(B, [List, Position]),
   (  B = [_|BT]    % is there something after this position?
   -> append(A, BT, Result)
   ;  Result = A
   ).

% func:reverse
builtin_reverse(Result, [List]) :-
   reverse(Result, List).

% func:index-of
builtin_index_of(Result, [List, Value]) :-
   findall(DI, 
	   (nth0(I, List, Value), data_number(DI,I)),
           Result).

% func:union
builtin_union(Result, Args) :-
	builtin_concatenate(R1, Args),
	builtin_distinct_values(Result, [R1]).

% func:distinct-values
builtin_distinct_values(Result, [List]) :-
	list_to_set(List, Result).


builtin_intersect([], []).
builtin_intersect(L, [L]).
builtin_intersect(Result, [L1,L2|Ls]) :-
	findall(I, (member(I, L1), member(I, L2)), R),
	builtin_intersect(Result, [R|Ls]).

builtin_except(Result, [Big, Small]) :-
	findall(I,
	        (member(I, Big),
                 \+ member(I, Small)
                ), 
		Result).