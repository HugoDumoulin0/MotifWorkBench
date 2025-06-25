# Timothée Premat and Hugo Dumoulin
# 28/03/2025

#Load/install packages
ipak <- function(pkg){
new.pkg <- pkg[!(pkg %in% installed.packages()[, "Package"])]
if (length(new.pkg))
    install.packages(new.pkg, dependencies = TRUE)
sapply(pkg, require, character.only = TRUE)
}

args <- commandArgs(trailingOnly = TRUE)
file_out <- args[1]
path_out <- args[2]

# usage
packages <- c('FactoMineR',
	'ggrepel',
	'factoextra',
	'dplyr')
ipak(packages)

# For DEBUG:
# file_out <- "./Patterns_results/R/25/motifs/motifsTexte_df_2025-06-25 10:23:35.158498.tsv"
# path_out <- "./Patterns_results/R/25/motifs/"

# print("file_out:")
# print(file_out)
# print("path_out:")
# print(path_out)

## Load data
df <- read.csv(file_out, sep="\t", header = TRUE, row.names = 1)
# df <- df %>% rename(Pattern = names(.)[1])
# rownames(df) <- df$Pattern

file_out <- sub("\\.tsv$", "", file_out)

## Compute CA
CA = CA(df, graph=F)

## Plot it!
### General plot
filename <- paste(file_out, "_AFC.bmp", sep = "")
  	plot_obj <- fviz_ca_col(CA,
    	shape.col = 16,
		labelsize = 4,
		repel = TRUE,
		col.col = "red") +
	theme_classic()
ggsave(filename, plot = plot_obj, width = 10, height = 10, dpi = 600)

#General plot with cos2 representing contribution
	#the value of the cos2 is between 0 and 1. A cos2 closed to 1 corresponds
	#to a column/row variables that are well represented on the factor map.
filename <- paste(file_out, "_AFC_cos2.bmp", sep = "")
	plot_obj <- fviz_ca_col(CA,
  		col.col = "cos2",
  		shape.col = 16,
  		labelsize = 4,
  		repel = TRUE,
  		gradient.cols = c("#00AFBB", "#E7B800", "#FC4E07")
	) +
  	theme_classic() +
  	guides(colour = guide_colourbar()) +  # Removes invalid position = "inside"
  	theme(
    	legend.position = c(0.01, 1),  # top-left inside the plot
    	legend.justification = c(0, 1),
    	legend.background = element_rect(fill = "white", color = "black"),
    	legend.margin = margin(0, 0, 0, 0)
  	)
ggsave(filename, plot = plot_obj, width = 10, height = 10, dpi = 600)

#-----------------------------------
# Functions to filter according to treshold
#-----------------------------------
# To do?

#-----------------------------------
# Check accuracy/explanatory power
#-----------------------------------

#Plot degree of variance explanation per axis
filename=paste(file_out, "_var_expl_per_axis.bmp", sep="")
plot_obj <- fviz_screeplot(CA,
	addlabels = TRUE) +
	theme_classic()
ggsave(filename, plot = plot_obj, width = 10, height = 10, dpi = 600)

#Take a look at representation accuracy
	#Get rows (MSE)
	row <- get_ca_row(CA)

	#Get the 10 heaviest contributing rows
	contrib_10_rows <- head(row$contrib, 10)
	write.table(contrib_10_rows,
		file = paste(file_out, "_contrib_10_patterns.txt", sep=""),
		sep = "\t",
        row.names = TRUE,
		col.names = NA)

	#Get cols (texts/subcorpora)
	col <- get_ca_col(CA)

	#Get the 10 heaviest contributing cols
	contrib_10_cols <- head(col$contrib, 10)
	write.table(contrib_10_cols,
		file = paste(file_out, "_contrib_10_texts.txt", sep=""),
		sep = "\t",
        row.names = TRUE,
		col.names = NA)

	#Plot it
	filename=paste(file_out, "_contrib_dim_1.bmp", sep="")
	plot_obj <- fviz_contrib(CA,
		choice ="col",
		axes = 1) +
  	theme_classic() +
  	guides(colour = guide_colourbar()) +  # Removes invalid position = "inside"
  	theme(
		axis.text.x = element_text(angle = 90, vjust = 0.5, hjust = 1),  # Rotate x-axis labels
    	legend.position = c(0.01, 1),  # top-left inside the plot
    	legend.justification = c(0, 1),
    	legend.background = element_rect(fill = "white", color = "black"),
    	legend.margin = margin(0, 0, 0, 0)
  	)
	ggsave(filename, plot = plot_obj, width = 10, height = 10, dpi = 600)

	filename=paste(file_out, "_contrib_dim_2.bmp", sep="")
	plot_obj <- fviz_contrib(CA,
		choice ="col",
		axes = 2) +
  	theme_classic() +
  	guides(colour = guide_colourbar()) +  # Removes invalid position = "inside"
  	theme(
		axis.text.x = element_text(angle = 90, vjust = 0.5, hjust = 1),  # Rotate x-axis labels
    	legend.position = c(0.01, 1),  # top-left inside the plot
    	legend.justification = c(0, 1),
    	legend.background = element_rect(fill = "white", color = "black"),
    	legend.margin = margin(0, 0, 0, 0)
  	)
	ggsave(filename, plot = plot_obj, width = 10, height = 10, dpi = 600)


# # Plot and measures for 2 dims with contrib threshold
# # source("plots_threshold.R")

# # Plot and measures for accuracy/explanatory power
# source("accuracy.R")
# # var_per_axis(AFC)

filename=paste(file_out, "_contrib10.bmp")
plot_obj <- fviz_ca_col(CA,
	select.col=list(contrib=10),
	col.var="contrib", 
    gradient.cols=c("#ffc2ca", "#ff0000"),
	shape.col=19,
	repel = TRUE) +
  	theme_classic() +
  	guides(colour = guide_colourbar()) +  # Removes invalid position = "inside"
  	theme(
    	legend.position = c(0.01, 1),  # top-left inside the plot
    	legend.justification = c(0, 1),
    	legend.background = element_rect(fill = "white", color = "black"),
    	legend.margin = margin(0, 0, 0, 0)
  	)
	ggsave(filename, plot = plot_obj, width = 10, height = 10, dpi = 600)

filename=paste(file_out, "_ind_contrib10.bmp")
plot_obj <- fviz_ca_row(CA,
	select.row=list(contrib=10),
	col.var="contrib",
	gradient.rows=c("#ffc2ca", "#ff0000"),
	shape.col=19,
	repel = TRUE) +
  	theme_classic() +
  	guides(colour = guide_colourbar()) +  # Removes invalid position = "inside"
  	theme(
    	legend.position = c(0.01, 1),  # top-left inside the plot
    	legend.justification = c(0, 1),
    	legend.background = element_rect(fill = "white", color = "black"),
    	legend.margin = margin(0, 0, 0, 0)
  	)
	ggsave(filename, plot = plot_obj, width = 10, height = 10, dpi = 600)

# bmp(filename=paste(var_name, "AFC_fviz2.bmp"),
#     width=2048, height=2048, res=200)
# plot_obj <- fviz_ca_col(AFC, shape.col=1, labelsize=4, repel=T, col.var="contrib", gradient.cols="#c30000", col.quali.sup="darkgreen")
#     print(plot_obj)
# dev.off()
# Redundant with AFC.bmp

filename=paste(file_out, "AFC_fviz3.bmp")
plot_obj <- fviz_ca_col(CA,
	select.col=list(contrib=10),
	pointsize="contrib",
	shape.col=19,
	repel=T) +
  	theme_classic() +
  	guides(colour = guide_colourbar()) +  # Removes invalid position = "inside"
  	theme(
    	legend.position = c(0.01, 1),  # top-left inside the plot
    	legend.justification = c(0, 1),
    	legend.background = element_rect(fill = "white", color = "black"),
    	legend.margin = margin(0, 0, 0, 0)
  	)
ggsave(filename, plot = plot_obj, width = 10, height = 10, dpi = 600)

filename=paste(file_out, "AFC_fviz3_ind.bmp")
plot_obj <- fviz_ca_row(CA,
	select.row=list(contrib=10),
	pointsize="contrib",
	label = "all",
	shape.row=19,
	repel=T) +
  	theme_classic() +
  	guides(colour = guide_colourbar()) +  # Removes invalid position = "inside"
  	theme(
    	legend.position = c(0.01, 1),  # top-left inside the plot
    	legend.justification = c(0, 1),
    	legend.background = element_rect(fill = "white", color = "black"),
    	legend.margin = margin(0, 0, 0, 0)
  	)
ggsave(filename, plot = plot_obj, width = 10, height = 10, dpi = 600)

filename=paste(file_out, "AFC_var_4.bmp")
plot_obj <- plot.CA(CA,
	invisible=c("row"),
	repel=T) +
  	theme_classic() +
  	guides(colour = guide_colourbar()) +  # Removes invalid position = "inside"
  	theme(
    	legend.position = c(0.01, 1),  # top-left inside the plot
    	legend.justification = c(0, 1),
    	legend.background = element_rect(fill = "white", color = "black"),
    	legend.margin = margin(0, 0, 0, 0)
  	)
ggsave(filename, plot = plot_obj, width = 10, height = 10, dpi = 600)

filename=paste(file_out, "AFC_fviz4_ind.bmp")
plot_obj <- fviz_ca_row(CA,
	select.row=list(contrib=30),
	pointsize="contrib",
	shape.row=19,
	repel=T) +
  	theme_classic() +
  	guides(colour = guide_colourbar()) +  # Removes invalid position = "inside"
  	theme(
    	legend.position = c(0.01, 1),  # top-left inside the plot
    	legend.justification = c(0, 1),
    	legend.background = element_rect(fill = "white", color = "black"),
    	legend.margin = margin(0, 0, 0, 0)
  	)
ggsave(filename, plot = plot_obj, width = 10, height = 10, dpi = 600)
