#!/bin/bash

dbname=nr
dbtype=prot
dbpartsize="400M"

#dbname=nt
#dbtype=nucl
#dbpartsize="400M"

#dbname=human_genomic
#dbtype=nucl
#dbpartsize="400M"

dbname=hg19
dbtype=nucl
dbpartsize="400M"

tmpdir=/local-scratch/iugalaxy/tmp
blastbin=/cvmfs/oasis.opensciencegrid.org/osg/projects/IU-GALAXY/rhel6/x86_64/ncbi-blast-2.2.28+/bin
mkdir -p $tmpdir

function download() {
    echo "downloading fasta"
    curl ftp://ftp.ncbi.nlm.nih.gov/blast/db/FASTA/$dbname.gz -o $tmpdir/$dbname.gz
    curl ftp://ftp.ncbi.nlm.nih.gov/blast/db/FASTA/$dbname.gz.md5 -o $tmpdir/$dbname.gz.md5
}

function check_md5() {
    echo "checking md5 sum"
    sum=$(cd $tmpdir && md5sum $dbname.gz) #sum=$(md5sum $dbname.gz | cut -c 1-32)
    dbsum=$(cat $tmpdir/$dbname.gz.md5)
    if [ ! "$sum" = "$dbsum" ]; then
        echo "ERROR: md5 doesn't match.. $sum is supposed to be $dbsum"
        return 1
    else
        echo "md5 sum good"
        return 0
    fi
}

function unzip() {
    echo "unzipping"
    gunzip $tmpdir/$dbname.gz -c > $tmpdir/$dbname.fasta
}

function split() {
    echo "removing old split dir"
    rm -rf $tmpdir/$dbname.splits

    echo "generating split"
    mkdir -p $tmpdir/$dbname.splits
    ./split_fasta.pl -i $tmpdir/$dbname.fasta -o $tmpdir/$dbname.splits/part -n $num_per_part
}

function zipsplit() {
    for part in $(ls $tmpdir/$dbname.splits)
    do
        echo "gzipping for $part"
        zippath=$tmpdir/$dbname
        mkdir -p $zippath
        #$blastbin/makeblastdb -in $tmpdir/$dbname.splits/$part -dbtype prot -out $dbpath/$dbname -hash_index
        gzip -c $tmpdir/$dbname.splits/$part > $zippath/$part.gz
    done
}

function makefulldb() {
    echo "making db"
    dbpath=$tmpdir/$dbname.db
    rm -rf $dbpath
    mkdir -p $dbpath
    $blastbin/makeblastdb -in $tmpdir/$dbname.fasta -dbtype $dbtype -out $dbpath/$dbname -max_file_sz $dbpartsize -parse_seqids -hash_index
}
function showdbinfo() {
    dbpath=$tmpdir/$dbname.db
    export BLASTDB=$dbpath
    echo "running blastdbcmd to get db size"
    $blastbin/blastdbcmd -db $dbname -info
}

function makedb() {
    for part in $(ls $tmpdir/$dbname.splits)
    do
        echo "making db for $part"
        dbpath=$tmpdir/$dbname.partdb
        mkdir -p $dbpath
        $blastbin/makeblastdb -in $tmpdir/$dbname.splits/$part -dbtype prot -out $dbpath/$part -hash_index
    done
}

function publish_parts() {
    pubdir=/local-scratch/public_html/iugalaxy/blastdb/$dbname
    echo "tarring db parts and publishing to " $pubdir
    rm -rf $pubdir
    mkdir -p $pubdir

    #loop through all dbparts
    cd $tmpdir/$dbname.db
    part=0
    while :
    do
        filepath=$dbname.`printf "%02d" $part`
        echo "testing $filepath"
        if [ -e "$filepath.psq" ] || [ -e "$filepath.nsq" ] ; then
                echo $filepath 
                tar -cz $filepath.* > $pubdir/$dbname.$part.tar.gz
        else
            break
        fi
        part=$((part+1)) 
    done

    echo "outputing list file"
    ls $pubdir/*.gz > $pubdir/list
    cd -

    echo "writing out blast.opt with some random numbers - please update using total residues (or total bases?)!"
    echo "-dbsize 11222333444" >> $pubdir/blast.opt

}

#download
#check_md5
#unzip
makefulldb
publish_parts
showdbinfo
