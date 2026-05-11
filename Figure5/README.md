## Figure 5 Reproducibility

In these scripts, we can simulate sequences, transform them, process them with mumemto.

The scripts should be run in this order:
1. `simulate_genomes_both.py`: simulate the genomes and transform them using MFT transform
2. `run_mumemto_all.py`: run mumemto on all of those sets of genomes (must have mumemto available)
3. `chain_mums.py`: chain the resulting mums together
4. `preprocess_mums`: analyze mums across all to make it easier to load

After that is done, `simulated_data_figs_realistic.ipynb` can be used to generate the final plot. Note that due to the scale of this data, it will be easier to skip some of the initial blocks and simply load in the summary_df.csv, which is the data we generated. 


Some notes:
- the paths in these files are all hard coded at the moment to our local computing cluster, so those will need to be updated to run locally