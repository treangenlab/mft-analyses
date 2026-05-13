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

The seqgen command that is run is the following:
`seq-gen -mGTR -l10000 -ofs -s{s} -z{seeds[i-1]} -y test < covid.tree`

This command runs a Jukes Cantor model with even site-specific mutation rates across the genome and outputs a fasta file of 100000bp sequences for each leaf in the tree. 



#### Generating the tree:
We generated the tree used for the phylogeny using 200 Sars-CoV-2 genomes. The accessions for these genomes are listed in "cov_genomes.txt". We downloaded each of these via ncbi. To generate the tree, we ran the default version of Parsnp2 using the following command:
`parsnp -g *.fna -r GCA_964157915.1_INEI121937_genomic.fna.ref -p 32 -o cov_tree`

This by default runs the following RAXML command on the resulting SNP multifasta. 
`raxmlHPC-PTHREADS -m GTRCAT -p 12345 -T [threads] -s [parsnp.snps.mblocks] -w [raxml_output_directory] -n OUTPUT`

This command infers a maximum-likelihood phylogeny using the GTR+CAT nucleotide substitution model in RAxML, where GTR models unequal substiturion rates between nucleotides and CAT approximates among-site rate heterogeneity for computational efficiency.

The command generates a tree in the output called `parsnp.tree`. `covid.tree` is a renamed version of this file. 