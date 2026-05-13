#### Figures 3-4

For the real viral genome experiments, we first downloaded viral genomes via ncbi datasets.

The sequence ids for all of these genomes are shared in `genome_lists` by name.

Once downloaded and placed in a folder `[organism]/n_[#]/nucleotide`, we then ran the following commands in order on each dataset. 

1. `transform_genomes.py`: this transforms all of the genomes once
2. `subsample_genomes.py`: this script subsamples the genomes from the original group
3. `run_mumemto.py`: this runs mumemto on every single subsampling
4. Then we used the seperate runner scripts to run the modified parsnp2 (for instance `measles_runner.sh`). Please see https://github.com/treangenlab/parsnp_external_mums for further instructions.
5. After parsnp2 was run, we then ran `filter_parsnp.py` to filter the LCBs. Note this script automatically calls the `filter_xmfa.py` script
6. Lastly we ran `parse_parsnp.py` to get stats for each alignment. 

After this, we then can run the notebook in `fig4.ipynb` which produces all relavant tables (including the Appendix Fig 2-3, as well as Fig 3-4 in the main text).

Note:
- the paths in these files are all hard coded at the moment to our local computing cluster, so those will need to be updated to run locally
