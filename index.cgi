#!/usr/bin/perl
use AppConfig;
use CGI;
use strict;
use warnings;

$SIG{'__DIE__'} = sub {
    print 'FATAL ERROR: '.$_[0]."\n";
    exit(1);
};

my @WARNINGS = ();
$SIG{'__WARN__'} = sub {
    push @WARNINGS, $_[0];
};

my $SCRIPT_NAME = $0;
$SCRIPT_NAME =~ s/^.*?(\w+\.(cgi|pl))$/$1/;

my $DEBUG = 0;

my $CONFIG_FILE = ($ENV{HOME} || ($ENV{DOCUMENT_ROOT} ? $ENV{DOCUMENT_ROOT}.'/..' : undef) || '.').'/.kraus';

my $config = AppConfig->new(
    {
        GLOBAL   => { ARGCOUNT => AppConfig::ARGCOUNT_ONE },
        PEDANTIC => 1,
    },
    css         => { DEFAULT => 'http://www.jay-jay.net/style.css' },
    smartcss    => { DEFAULT => 'smartphone.css' },
);
$config->_debug(1) if ($DEBUG);
# CONFIG_FILE is optional but if it exists it must contain valid options
if (-f $CONFIG_FILE) {
    unless ($config->file($CONFIG_FILE)) {
        print_raw_header();
        print_raw_errors() if ($DEBUG);
        die "failure reading config file";
    }
}

my $PARAM_FORMAT = 'format';
my $PARAM_HELP   = 'help';
my $PARAM_OFFSET = 'offset';

my $SECONDS_PER_DAY = 24 * 60 * 60;

# -----------------------------------------------------------------------------

if (defined $ARGV[0] and $ARGV[0] eq '-s') {
    my $limit = $ARGV[1] || 30;
    foreach my $o (0..$limit) {
        printf("%03d\t%d\n", $o, calc_location($o));
    }
    exit;
}

my $cgi = new CGI;
# --- read url params ---------------------------
my $format = $cgi->param($PARAM_FORMAT) || 'html';
my $help   = $cgi->param($PARAM_HELP);
my $offset = $cgi->param($PARAM_OFFSET) || 0;
# validate input
$format =~ tr/a-zA-Z/_/cs;
$offset =~ tr/-0-9/0/cs;
force_help() if (defined $help);
force_help("invalid format argument") unless ($format =~ m/^(raw|html)$/);
force_help("invalid offset argument") unless ($offset =~ m/^-?[0-9]+$/);

# --- core processing ---------------------------
eval "print_${format}_header()";
if ($help) {
    eval "print_${format}_help()";
}
else {
    eval "print_${format}_location($offset)";
}
eval "print_${format}_errors()";
eval "print_${format}_footer()";

exit 0;

# -----------------------------------------------------------------------------

sub force_help {
    warn $_[0] if (@_);
    $help = 1;
    $format = 'raw';
}

sub print_raw_header {
    print "Content-type: text/plain\r\n\r\n";
}

sub print_html_header {
    print "Content-type: text/html\r\n\r\n";
    my $css = $config->css();
    my $smartcss = $config->smartcss();

    print <<EOT;
<!DOCTYPE html
        PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
         "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en-US" xml:lang="en-US">
<head>
<title>K.R.A.U.S. - Kaffee-Runde auf unterschiedlichen Stockwerken</title>
<link rel="stylesheet" type="text/css" href="$css" />
<link rel="stylesheet" type="text/css" href="$smartcss" media="only screen and (min-device-width: 320px) and (max-device-width: 480px)" />
<meta name="viewport" content="width = 400" />

<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
</head>
<body>
<div class="page">
EOT
}

# -----------------------------------------------------------------------------

sub print_raw_footer {
}

sub print_html_footer {
    print <<EOT;
</div>
</body>
EOT
}

# -----------------------------------------------------------------------------

sub print_raw_errors {
    return unless (@WARNINGS);
    print "\nWarnings:\n";
    foreach my $line (@WARNINGS) {
        print "$line\n";
    }
}

sub print_html_errors {
    return unless (@WARNINGS);
    print "<hr/>\n<b>Warnings:</b><br/>\n";
    foreach my $line (@WARNINGS) {
        print "$line<br/>\n";
    }
}

# -----------------------------------------------------------------------------

sub print_raw_help {
    print <<EOT;

PARAMETERS

    help=1
        Produces this help text.

    format={html|raw}
        Defines the output format. The raw output is meant to be used for programs that need to fetch the location for further processing.

    offset=N
        Specifies the date to be queried relative to the current date. Negative values are allowed. Default is zero, i.e. the current date.

EOT
}

sub print_raw_location {
    my $subname = (caller(0))[3];
    die "$subname: wrong number of arguments" unless (@_ == 1);
    my ($offset) = @_;

    print calc_location($offset)."\n";
}

sub print_html_location {
    my $subname = (caller(0))[3];
    die "$subname: wrong number of arguments" unless (@_ == 1);
    my ($offset) = @_;

    my ($year, $month, $day) = get_date($offset);

    my $location = calc_location($offset);

    my $prev = ($offset - 1);
    my $next = ($offset + 1);

    if (defined $format and $format eq 'raw') {
        print "$location\n";
    }
    else {
        print <<EOT;
    <p>
        Am $day.$month.$year treffen wir uns im <b>$location. OG</b> -- falls belegt, im n&auml;chsth&ouml;heren freien Stockwerk.
    </p>
    <p>
        <a href="$SCRIPT_NAME?$PARAM_OFFSET=$prev">[&lt;&lt;&lt;&lt;&lt;]</a>
        &nbsp;&nbsp;
        <a href="$SCRIPT_NAME">[heute]</a>
        &nbsp;&nbsp;
        <a href="$SCRIPT_NAME?$PARAM_OFFSET=$next">[&gt;&gt;&gt;&gt;&gt;]</a>
    </p>
    <p>
        <a href="$SCRIPT_NAME?$PARAM_HELP=1">[Hilfe zu Parametern]</a>
    </p>
EOT
    }
}

# -----------------------------------------------------------------------------

sub calc_location {
    my $subname = (caller(0))[3];
    die "$subname: wrong number of arguments" unless (@_ == 1);
    my ($offset) = @_;

    my ($year, $month, $day) = get_date($offset);

    srand($day * $day + $month);

    return int(rand(8)) + 1;
}

# -----------------------------------------------------------------------------
# get_date(Integer $diff)
# Calculates the date of the day that was $diff days before or after the
# current date.
# Returns:
#       a 3-element list (year, month, day)
sub get_date {
    die "argument (integer number) expected" unless (@_ == 1);
    my ($diff) = @_;
    die "not an integer number: '$diff'" unless ($diff =~ m/^-?\d+$/);

    my $now_ts = time;
    # set time to noon to avoid problems with 23h-days on standard time to DST transition
    my ($now_sec, $now_min, $now_hour) = localtime($now_ts);
    $now_ts -= (($now_hour - 12) * 60 * 60) + ($now_min * 60) + $now_sec;

    my @then = localtime($now_ts + ($diff * $SECONDS_PER_DAY));

    return (1900 + $then[5], 1 + $then[4], $then[3]);
}
