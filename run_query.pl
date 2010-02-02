
% -*- mode: prolog -*-

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
