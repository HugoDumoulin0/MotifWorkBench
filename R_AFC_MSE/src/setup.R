#-----------------------------------------------
# Install and load packages
#-----------------------------------------------

# ipak function: install and load multiple R packages.
# check to see if packages are installed. Install them if they are not, then load them into the R session.

ipak <- function(pkg){
new.pkg <- pkg[!(pkg %in% installed.packages()[, "Package"])]
if (length(new.pkg))
    install.packages(new.pkg, dependencies = TRUE)
sapply(pkg, require, character.only = TRUE)
}

# usage
packages <- c('FactoMineR',
	'ggrepel',
	'factoextra',
	'tcltk')
ipak(packages)

#-----------------------------------------------
# Interactively ask for input file
#-----------------------------------------------
	#Define default folder
	default_folder <- "../data/*"

	#Filter formats
	Filters_file_format <- matrix(c("TSV", ".tsv"),
									1, 2, byrow = TRUE)

	#ask user for data file
	table <- tk_choose.files(default = file.path(default_folder),
		caption = paste('Select input table'),
		multi = FALSE,
		filter = Filters_file_format)

	#read it
<<<<<<< Updated upstream
	table = read.csv(table, sep="\t", header=T, row.names="motifs_str", encoding="UTF-8")
=======
<<<<<<< HEAD
	table = read.csv(table, sep="\t", header=T, row.names=1, encoding="UTF-8")
=======
	table = read.csv(table, sep="\t", header=T, row.names="motifs_str", encoding="UTF-8")
>>>>>>> main
>>>>>>> Stashed changes

#-----------------------------------------------
# Interactively ask for prefix for naming files
#-----------------------------------------------

	#Ask the user for filename prefix
	var_name <- readline(prompt="Enter prefix for naming files:")

		# If no name is provided, results to default.
		if (is.null(var_name) || var_name == "")
			{
		    	var_name <- "no-name"  # Set default name if var_name is NULL
		  	}
