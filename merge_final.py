#!/usr/bin/env python

"""

A custom made script to merge the XML blast outputs
when queries are run in parallel by input-choping.

Copied and adapted from https://bitbucket.org/peterjc/galaxy-central/src/5cefd5d5536e/tools/ncbi_blast_plus/blast.py

Tested working with BLAST 2.2.28+

The fields:
  <Iteration_iter-num></Iteration_iter-num>
  <Iteration_query-ID></Iteration_query-ID>
should not be used from the merged file.
"""

# Modules #
import sys, os, glob, gzip
output_dir = sys.argv[1]

output_path = output_dir+"/merged.xml.gz"
output = gzip.open(output_path, "w")
print "final output:",output_path

count = 0 #start with block 0
while True:
	path = output_dir+"/block_"+str(count)+".merged.xml"
	#print "testing",path
	if os.path.exists(path):
		handle = open(path, "r")
	else:
		#try userdb (pre-merged) content"
		#path = output_dir+"/block_"+str(count)+".result.gz"
		path_gz = output_dir+"/block_"+str(count)+".result.gz"
		path = output_dir+"/block_"+str(count)+".result"
		if os.path.exists(path_gz):
			#python gzip.open() / readline is slow.. just unzip first
			os.system("gunzip -f "+path_gz)
			#handle = gzip.open(path, "r")
			handle = open(path, "r")
		else:
			break #failed to find - stop
	print "processing",path

        header = handle.readline()
        if not header:
            raise Exception("BLAST XML file '%s' was empty" % path)
        if header.strip() != '<?xml version="1.0"?>':
            raise Exception("BLAST file '%s' is not an XML file" % path)
        line = handle.readline()
        header += line
        if line.strip()[0:59] != '<!DOCTYPE BlastOutput PUBLIC "-//NCBI//NCBI BlastOutput/EN"':
            raise Exception("BLAST file '%s' is not a valid XML file" % path)
        while True:
            line = handle.readline()
            if not line:
                raise Exception("BLAST XML file '%s' ended prematurely" % path)
            header += line
            if "<Iteration>" in line: break
            if len(header) > 10000:
                raise Exception("BLAST file '%s' has a too long a header" % path)
        if "<BlastOutput>" not in header:
            raise Exception("BLAST XML file '%s' header's seems bad" % path)
        if count == 0:
            output.write(header)
            old_header = header
        elif old_header[:300] != header[:300]:
            raise Exception("BLAST XML headers don't match" % path)
        else: output.write("    <Iteration>\n")
	#print "loading iterations"
        for line in handle:
            #if "</BlastOutput_iterations>" in line: break
            if line.find("</BlastOutput_iterations>") != -1: 
	    	break
            output.write(line)
	#print "done loading iterations"

	handle.close()

        print "removing",path
	os.remove(path)

	count+=1

if count > 0:
	#output the tail
	output.write("</BlastOutput_iterations>\n")
	output.write("</BlastOutput>\n\n")
else:
	print "Couldn't find any blast results to merge.."
	sys.exit(1)

output.flush()
output.close()


