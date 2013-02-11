#!/usr/bin/perl
#Do what you want with this
#Created by Tom Powell <zifnab@zifnab06.net>

use Time::localtime;
use Switch;

#Modify these to fit your situation
my $REQ_DOMAIN = "somewhere.org";
my $admin = "admin@admin.localhost";
my $VALID_EMAIL = "SomePlace";
my $ACCESS_CODE = "secureCode";
my $EMAIL_BODY = "Email Body";
my $SUBJECT = "New Account Creation";



#Don't modify past this if you don't know what you are doing
#Better yet, don't use this if you don't understand what it does

print "Content-type: text/plain\n\n";
#Clean PATH for SUID scripts
delete @ENV{qw(IFS CDPATH ENV BASH_ENV)}; 
$ENV{PATH} = "/bin:/usr/bin:/usr/sbin";

#Get POST/GET
if ($ENV{'REQUEST_METHOD'} eq "GET") {

        $request = $ENV{'QUERY_STRING'};

} elsif ($ENV{'REQUEST_METHOD'} eq "POST") {
        read(STDIN, $request,$ENV{'CONTENT_LENGTH'})
                || die "Could not get query\n";
}


#split $request up into @parameter_list
@parameter_list = split(/&/,$request);
foreach (@parameter_list) {
    s/\+/ /g;
    s/%([0-9A-F][0-9][A-F])/pack("c",hex($1))/ge;

    ($name, $value) = split('=');
    $passed{$name} = $value;
}


#Get paramaters
$email = $passed{"email"};
$code = $passed{"code"};
$first = $passed{"first"};
$last = $passed{"last"};
$email =~ ( s/%40/@/g );
$pass = randomPassword();
($username, $domain) = split('@',$email);

if ($first =~ /^([-\@\w.]+)$/) {
	$first = $1; 			# $data now untainted
} else {
	print "You either missed a field, or had an invalid character in your query.";
	die "Bad data in '$first'"; 	# log this somewhere
}

if ($last =~ /^([-\@\w.]+)$/) {
        $last = $1;                    # $data now untainted
} else {
        print "You either missed a field, or had an invalid character in your query.";
        die "Bad data in '$last'";      # log this somewhere
}

$username = lc($username);
$username =~  /(.*)/;
$username = $1;

#We need to be sure that they are a student, so we are using their EDU email. Then, check to see if they have the correct code. 
if ($domain ne $REQ_DOMAIN){
	print "You must use your $VALID_EMAIL email";
}elsif ($code ne $ACCESS_CODE) {
	print "You have an invalid access code.";
} else {
	createAccount(); #do all the work
	#createAccount will die() if an error occured. 
	sendEmail();
}

sub sendEmail {
	
	if ($debug) {
		print "From: AccountCreation\@$cs.{REQ_DOMAIN}\n";
		print "Date: ".ctime()."\n";
		print "To: ". $email . "\n";
		print "Subject: ${EMAIL_SUBJECT}\n";
		print "\n";
		print $EMAIL_BODY;
	} else {
	#send the email to them with said password (makes sure they used a valid email)
		open(SM, "|/usr/sbin/sendmail -t");
		print(SM "FROM: AccountCreation\@cs.{REQ_DOMAIN}\n");	
		print(SM "Date: ".ctime()."\n");
		print(SM "To: " . $email . "\n");
		print(SM "Subject: ${subject}\n");
		print(SM "\n");
		print(SM "$EMAIL_BODY\n");
		close(SM);
	}

}

#randomPassword() returns a 6 letter string, used for their original password.
sub randomPassword {
	my $password;
	my $_rand;
	my $password_length = 5;
	my @chars = split(" ","a b c d e f g h j k m n p q r t A B C D E F G H J K L M N P Q R T 2 3 4 5 6 7 8 9");
	srand;
	for (my $i=0; $i <= $password_length ;$i++) {
	    $_rand = int(rand 41);
            $password .= $chars[$_rand];
	}
	return $password;
}

sub createAccount {
	#make a password crypt, use DES. Any account with '2a' as the salt can safetly be deleted after a time
	$crypted=crypt($pass, "2a");
	#This line does all the magic, useradd -g (group) -k (skel) -d (homedir) -m (makehome) -N (no user group) -p (crypted pass) -c (name) username
	$cmd="/usr/sbin/useradd -g students -k /etc/skel/ -d /home/students/$username -m -N -p $crypted -c \"${first} ${last}\" $username";
	system($cmd);
	$return = $? >> 8;
	switch($return) {
		case 0 {print "Your account has been successfully created. You should recieve an email at ${email} with your password shortly.\n";}
		case 9 {$error = "This account exists already. Did you create it already? Error code 9"; print $error; die $error;}
		case 12 {print "Your account has been (almost) been created. Your home directory has not been created. Please email ${admin} and show them this error. Error code 12.";}
		default {$error = "Something happened that shouldn't have, we apologize for that. Please email ${admin} and show them this error. Error code ${return}"; print $error; die $error;}
	}
}
