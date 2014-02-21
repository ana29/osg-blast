#!/bin/bash

echo "merging dbparts"
query_block=0
while [ -f output.qb_$query_block.db_0 ]
do
    echo "merging query block $query_block"
    ls output.qb_$query_block.*
    sort output.qb_$query_block.* > merged.qb_$query_block
    query_block=$((query_block+1))
done

echo "merging query blocks"
sort merged.qb_* > merged
