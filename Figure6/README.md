## Figure 6 Reproducibility

In these scripts, we can simulate sequences, transform them, process them with mumemto.

The scripts should be run in this order:
1. `simulate_along_phylogeny.py`: simulate the genomes using `covid.tree` and seq-gen (command is called directly, so must have seqgen available)
2. `subsample_genomes_cov.py`: subsample the genomes into the sets of genomes
3. `transform_genomes.py`: transform all of the genomes using the MFT transformation
4. `run_mumemto_all.py`: run mumemto on all of those sets of genomes (must have mumemto available)
5. `chain_mums.py`: chain the resulting mums together
6. `preprocess_mums`: analyze mums across all to make it easier to load

After that is done, `simulated_data_figs_realistic.ipynb` can be used to generate the final plot


Some notes:
- the paths in these files are all hard coded at the moment to our local computing cluster, so those will need to be updated to run locally