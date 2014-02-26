## OSG Blast (V2)

ncbi-blast workflow submission script

osg-blast submits a workflow to run blast search on a large input queries with a large database. 
osg-blast is intended to run on Open Science Grid, and via osg-xsede submit host.

# Installation

```
npm install osg-blast
```

# Usage

Step 1. Place some fasta input query under an empty directory.

Or you can use following example.. (input.fasta)

```
>comp7_c0_seq1 len=222 path=[382:0-221]
CCACTCGGAAATCTCATCTGAGAACACCGACAACCGGACCATTCGTGCGACGGCGGAGTA
CAAGCCCGGCTCGGGCCTGCACTACTTTGAAGTCGAATCCCGCTGCCCCAAGGAGGTGCA
ATACCACCCGTACGTCGGTCTGTGCTCCACCAATGAGGCCGTGCCGGTGGAGAAGATGCT
GATGTGGCTCAGCGATCTGTGCTACGCCTACGGCGGGGAAGG
>comp55_c0_seq1 len=228 path=[206:0-227]
GCCGCGTATTCTCGTAGCATGTCCGGGGTGGGCTGGGTCTGCGCTCCATTCATCACCGCC
ACTTGGGGGAGACCATGCTCCTTCAGATCGCGCTCCAAGGCGTCCATCGCCCCCATACCT
TTAGTATGGTTCCCCGAATAGATGACTAAGAACTTACATCCCGCGAGTTGACGATACAGA
CGGCTCCACGGCTGATCGAGCGGTTTGAGCTTCTCCAGCCAGCCCATA
>comp129_c0_seq1 len=214 path=[317:0-213]
GAGGGAACTCTTGGTTGCTCTGAATGACCAGTATGCTGAGGTAGTTGTCCAGGGTGTACT
TGTGAAACTCTTGGATCCACTGGTCTATCAGCGTGGCGGGAACCACTATCAATGTCGCCG
CGGAAAGATACATTTGCATCGCCAGAGGGAGGCCCTTCCGAGGCGTGCCATCGCCAGAGG
TGCCACGGGCTTGGGCGGCACTTTCCGAAGAACT

```

Step 2. Create config.json containing something like following

```
{
    "project": "CSIU",
    "user": "hayashis",

    "input": "input.fasta",
    "db": "oasis:dmel-all-chromosome-r5.55-2",
    "blast": "blastn",
    "blast_opts": "-evalue 0.001 -outfmt 6 -best_hit_score_edge 0.05 -best_hit_overhang 0.25 -perc_identity 98.0"
}

```

You need to specify the project that you have access on your submit host.

Step 3. Run osg-blast

```
osg-blast config.json
```

osg-blast will start running some tests, then submits jobs (there could be many thousands, depending on the size of your
database, and input query, and your input parameters).

To abort your job, simply hit CTRL+C (or do kill $pid). 

Step 4. Merge output

osg-blast will generate output files for each jobs under ./output directory. You can use osg-blast's merge script to merge all of your output into a single output file.

```
$ cd output
$ osg-blast-merge6
merging dbparts
merging query block 0
output.qb_0.db_0   output.qb_0.db_11  output.qb_0.db_14  output.qb_0.db_2  output.qb_0.db_5  output.qb_0.db_8
output.qb_0.db_1   output.qb_0.db_12  output.qb_0.db_15  output.qb_0.db_3  output.qb_0.db_6  output.qb_0.db_9
output.qb_0.db_10  output.qb_0.db_13  output.qb_0.db_16  output.qb_0.db_4  output.qb_0.db_7
merging query blocks

```

# Details

osg-blast splits your input queries, and use DB that is split into mutiple chunks (1G compressed each), and submits
all jobs on local queue in the order of required DB part number (to maximize squid hits). Any failed job will be
analyzed to see if it can be re-submitted elsewhere, and if not, then abort the entire workflow.

Every blast execution is unique, and amount of memory / cpu resources required to run blast depends on the type
of input query, db, and input parameters, etc.. so osg-blast first submits some test jobs in order to determine 
how large the each input block should be. 

osg-blast uses some hosted DB (such as those DB published by NCBI) so you don't have to have them available with 
your job. osg-blast will use ones published via OSG's OASIS.

If you want to provide your own database, you can do so, but you need to make it available via some webserver where
each job can download from (through squid).


# License

MIT?


