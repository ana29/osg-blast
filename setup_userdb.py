#!/usr/bin/python

import sys
import os,subprocess
import time
import shutil
import urllib
import re
import socket
import gzip

if len(sys.argv) != 7:
    print "incorrect number of arguments"
    sys.exit(1)

portalid=sys.argv[1]
project=sys.argv[2]
query_path=sys.argv[3]
blast_type=sys.argv[4]
user_blast_opt=sys.argv[5]
rundir=sys.argv[6]

#TODO - need to adjust this based on the size of the input db.. user provided db tends to be small..
#for blastn, which ignores BATCH_SIZE, anything more than 1000 will cause frequent sigkill(128+9).. too much memory?
#for non-blastn, BATCH_SIZE should limit the amount of memory used so you can probably go upto 4000
#block_size=500 #500 should use 1.5G - 2G (occationally 4G..)

block_size=40000 #50000 runs out of memory occastionally

bin_path = "http://osg-xsede.grid.iu.edu/scratch/iugalaxy/blastapp/ncbi-blast-2.2.28+/bin"

#rundir = "/N/dcwan/scratch/iugalaxy/rundir/"+str(time.time())
#rundir = "/local-scratch/hayashis/rundir/"+str(time.time())

#create rundir
#if os.path.exists(rundir):
#    print "#rundir already exists.."
#    sys.exit(1)
#else:
#    os.makedirs(rundir)
os.mkdir(rundir+"/log")
os.mkdir(rundir+"/output")

#parse input query
input = open(query_path)
queries = []
query = ""
name = ""
for line in input.readlines():
    if line[0] == ">":
        if name != "":
            queries.append([name, query])
        name = line
        query = ""
    else:
        query += line
if name != "":
    queries.append([name, query])
input.close()

#split queries into blocks
inputdir=rundir+"/input"
os.makedirs(inputdir)
block = {}
count = 0
block = 0
for query in queries:
    if count == 0:
        if block != 0:
            outfile.close() 
        outfile = gzip.open("%s/block_%d.gz" % (inputdir, block), "w")
        block+=1
    count+=1
    if count == block_size:
        count = 0

    outfile.write(query[0])
    outfile.write(query[1])
if outfile:
    outfile.close()

#I don't know how to pass double quote escaped arguments via condor arguemnts option
#so let's pass via writing out to file.
#we need to concat user blast opt to db blast opt
blast_opt = file(rundir+"/blast.opt", "w")
blast_opt.write(user_blast_opt)

#500 will cause memory usage issue with merge.py
#TODO - update on merge.py as well to match this (should be configurable..)
#increasing max_target_seqs increases virtual memory usage. NCBI article suggests to set ulimit, or use BATCH_SIZE env.
#for now, let's set this to small (compared to default 500) to workaround the memory issue
#http://www.ncbi.nlm.nih.gov/books/NBK1763/
blast_opt.write(" -max_target_seqs 50 -window_size 32000") 
blast_opt.close()

#host db.tar.gz in userdb directory
print "calculating md5sum"
proc = subprocess.Popen(["md5sum", rundir+"/db.tar.gz"], stdout=subprocess.PIPE)
(out, err) = proc.communicate()
out_split = out.split(" ")
db_filename=out_split[0]+".db.tar.gz"
public_path="/local-scratch/public_html/iugalaxy/userdb"
print "moving db to "+public_path
os.system("mv "+rundir+"/db.tar.gz "+public_path+"/"+db_filename)

#output condor submit file for running blast
dag = open(rundir+"/blast.dag", "w")
#merge_subs = []
#for query_block in os.listdir(inputdir):

sub = open(rundir+"/query.sub", "w")

if socket.gethostname() == "osg-xsede.grid.iu.edu":
	sub.write("#for osg-xsede\n")
	sub.write("universe = vanilla\n") #for osg-xsede
else:
	sub.write("universe = grid\n") #on bosco submit node (soichi6)

sub.write("notification = never\n")
sub.write("ShouldTransferFiles = YES\n")
sub.write("when_to_transfer_output = ON_EXIT\n\n") 

#sub.write("Requirements = (GLIDEIN_ResourceName =!= \"cinvestav\") && (GLIDEIN_ResourceName =!= \"Nebraska\") && (Memory >= 2000) && (Disk >= 500*1024*1024)\n") #cinvestav has an aweful outbound-squid bandwidth (goc ticket 17256)
sub.write("Requirements = (GLIDEIN_ResourceName =!= \"cinvestav\") && (Memory >= 2000) && (Disk >= 500*1024*1024)\n") #cinvestav has an aweful outbound-squid bandwidth (goc ticket 17256)

sub.write("periodic_hold = ( ( CurrentTime - EnteredCurrentStatus ) > 10800) && JobStatus == 2\n")  #max 3 hours
sub.write("periodic_release = ( ( CurrentTime - EnteredCurrentStatus ) > 60 )\n") #release after 60 seconds
sub.write("on_exit_hold = (ExitBySignal == True) || (ExitCode != 0)\n\n") #stay in queue on failures

sub.write("executable = blast_wrapper_userdb.sh\n")
sub.write("output = log/block_$(Process).cluster_$(Cluster).out\n")
sub.write("error = log/block_$(Process).cluster_$(Cluster).out\n")
sub.write("log = log/blast.log\n")

sub.write("+ProjectName = \""+project+"\"\n") #only works if submitted directly on osg-xsede (use ~/.xsede_default_project instead)
sub.write("+PortalUser = \""+portalid+"\"\n") 

sub.write("transfer_output_files = output\n")

#TODO - I should probably compress blast executable and input query block?
sub.write("transfer_input_files = blast.opt,input/block_$(Process).gz\n")
sub.write("arguments = "+bin_path+" "+blast_type+" $(Process) output/block_$(Process).result http://osg-xsede.grid.iu.edu/scratch/iugalaxy/userdb/"+db_filename+"\n")

#description to make condor_q looks a bit nicer
sub.write("+Description = \""+blast_type+" user_db block_$(Process)\"\n")

sub.write("\nqueue "+str(block)+"\n")
sub.close()

#copy blast_wrapper.sh
shutil.copy("blast_wrapper_userdb.sh", rundir)

shutil.copy("merge_final.py", rundir)

#copy dagman config
shutil.copy("dagman.config", rundir)

dag.write("CONFIG dagman.config\n")
dag.write("JOB query query.sub\n")
dag.write("RETRY query 10\n") #too many?
dag.write("JOB final final.sub\n")
dag.write("PARENT query CHILD final\n")
dag.write("RETRY final 3\n")

#output final.sub
fsub_name = "final.sub"
fsub = open(rundir+"/"+fsub_name, "w")
fsub.write("universe = local\n")
fsub.write("notification = never\n")
fsub.write("executable = merge_final.py\n")
fsub.write("arguments = "+rundir+"/output\n")
fsub.write("output = log/final.out\n")
fsub.write("error = log/final.out\n")
fsub.write("log = log/final.log\n")
fsub.write("queue\n")

dag.close()

#output rundir
#print rundir
