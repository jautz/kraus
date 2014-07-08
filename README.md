K.R.A.U.S.
==========

Abstract
--------

Determines the "floor of the day" on which my co-workers and me meet for coffee.

The acronym stands for the German phrase _Kaffee-Runde auf unterschiedlichen Stockwerken_.

Runtime Environment
-------------------

To run this script you need Perl5 with modules CGI and AppConfig.
CGI.pm has been included in the Perl distribution since Perl 5.4.
Thus, on Debian derivates, this will prepare the runtime environment:

`apt-get install perl libappconfig-perl`

Usually you will run this script inside a webserver like Apache with `mod_perl`.

Debugging
---------

You can run this script directly from the command line using the CGI module's
debugging feature (see perldoc CGI section DEBUGGING for details):

`./index.cgi format=raw offset=2`

Finally, to find out whether the pseudo-random location selector distributes equally
there is a simulation mode that prints the selections for the next days to stdout:

`./index.cgi -s [default=30]`

For example, this produces the number of selections for each floor in the next 500 days:

    ./index.cgi -s 500 | awk '{print $2}' | sort | uniq -c
     56 1
     56 2
     60 3
     69 4
     69 5
     68 6
     59 7
     64 8

Well, the distribution is far from perfect but at least this script yields reproducible
results without a central storage.
