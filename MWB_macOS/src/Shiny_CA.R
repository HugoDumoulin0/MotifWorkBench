
# Timothée Premat and Hugo Dumoulin 
# 24/05/2026
# Modifié le 11/06/2026 par @jcharlesDS
# updated by Timothée Premat on the 10/10/2026

#--------------------------------------------------------------
# Python/R interface
#--------------------------------------------------------------
args <- commandArgs(trailingOnly = TRUE)

path = args[1]

dir.create("./Patterns_results/CA_plots", recursive = TRUE, showWarnings = FALSE)

rep_name=path

#--------------------------------------------------------------
# BASIC R STUFF
#--------------------------------------------------------------

#Load/install packages, input file and set variables
ipak <- function(pkg){
options(repos = c(CRAN = "https://cloud.r-project.org"))

# Utiliser un répertoire utilisateur pour les packages R
user_lib <- Sys.getenv("R_LIBS_USER")
if (!dir.exists(user_lib)) {
    dir.create(user_lib, recursive = TRUE)
}
.libPaths(c(user_lib, .libPaths()))

new.pkg <- pkg[!(pkg %in% installed.packages()[, "Package"])]
if (length(new.pkg)) {
    cat("Installation des packages R:", paste(new.pkg, collapse=", "), "\n")
    install.packages(new.pkg, dependencies = TRUE, lib = user_lib)
}

sapply(pkg, require, character.only = TRUE)
}

# usage
packages <- c('FactoMineR',
	            'ggrepel',
	            'factoextra',
              "glue",
              "shiny",
              "DT",
              "ggplot2",
              "plotly",
              "dplyr",
              "tidyverse",
              "shinyjs",
              "viridis",
              "scales",
              "fastcluster",
              "jsonlite",
              "bslib",
              "shinyBS",
              "bsicons"
              )
ipak(packages)

# ---- Deal with file selection ---- #
args <- commandArgs(trailingOnly = TRUE)
json_input <- args[1]

last_analysis_file <- file.path(dirname(normalizePath(json_input)), "last_analysis.json")
print(last_analysis_file)

patterns_dir <- if (file.exists(last_analysis_file)) {
  fromJSON(last_analysis_file)$patterns_results
} else {
  file.path(getwd(), "Patterns_results")
}

ca_plots_dir <- file.path(patterns_dir, "CA_plots")
dir.create(ca_plots_dir, recursive = TRUE, showWarnings = FALSE)

# Load JSON from python
datasets <- fromJSON(paste(json_input, collapse = ""))


print(datasets)

normal_dataset_names <- names(datasets)[!grepl("_specifs_", names(datasets))]
specif_dataset_names <- names(datasets)[grepl("_specifs_", names(datasets))]
metadata_name <- unique(sub("_.*", "", normal_dataset_names))

text_json <- file.path(patterns_dir,"text_sizes.json")
print(text_json)
text_size <- fromJSON(text_json)

# Build size (nb of tokens) of each value of each metadata column, summing the
# sizes of its texts, e.g. metadata_sizes$genre["news"]. Every column of the
# metadata file is covered (whatever was selected in python), id included:
# metadata_sizes$id gives the size of each text
analysis_info <- fromJSON(
  file.path(dirname(patterns_dir), "analysis_info.json")
)
metadata_path <- analysis_info$config$path_metadata

metadata <- read.csv(
  metadata_path,
  sep = "\t",
  colClasses = "character",
  check.names = FALSE
)
id_col <- names(metadata)[1]
texts_sizes <- unlist(text_size$texts)
metadata$size <- texts_sizes[metadata[[id_col]]]
if (any(is.na(metadata$size))) {
  warning("Texts without size in text_sizes.json: ",
          paste(metadata[[id_col]][is.na(metadata$size)], collapse = ", "))
}
metadata_cols <- setdiff(names(metadata), "size")
metadata_sizes <- lapply(metadata_cols, function(col) {
  tapply(metadata$size, metadata[[col]], sum, na.rm = TRUE)
})
names(metadata_sizes) <- metadata_cols
print("Metadata sizes:")
print(metadata_sizes)




print("Metadata name:")
print(metadata_name)

has_user_input_list <- grepl("user_input_listTrue", names(datasets))
print("Has user input list:")
print(has_user_input_list)

name_user_input <- names(datasets)[grepl("user_input_listTrue", names(datasets))]
user_input_value <- sub(".*user_input_listTrue([^_]+).*", "\\1", name_user_input)
print("User input value:")
print(user_input_value)



has_specifs <- length(specif_dataset_names) > 0
print("Has specifs:")
print(has_specifs)

name_motifs <- normal_dataset_names[grepl("motif", normal_dataset_names, ignore.case = TRUE)]
has_motifs <- name_motifs
print("Has motifs:")
print(has_motifs)

minsup <- unique(sub(".*_([^_]+)_[^_]+_[^_]+_[^_]+$", "\\1", name_motifs))
print("Minsup:")
print(minsup)

gapmin <- unique(sub(".*_[^_]+_([^_]+)_[^_]+_[^_]+$", "\\1", name_motifs))
print("Gapmin:")
print(gapmin)

gapmax <- unique(sub(".*_[^_]+_[^_]+_([^_]+)_[^_]+$", "\\1", name_motifs))
print("Gapmax:")
print(gapmax)

itemsetmin <- unique(sub(".*_[^_]+_[^_]+_[^_]+_([^_]+)$", "\\1", name_motifs))
print("Itemsetmin:")
print(itemsetmin)

pattern_representations <- unique(ifelse(

  grepl("motif", normal_dataset_names, ignore.case = TRUE),
  "motif",
  sub(".*_([^_]+)$", "\\1", normal_dataset_names)
))



pattern_representation <- pattern_representations
minsup_display <- minsup
gapmin_display <- gapmin
gapmax_display <- gapmax
itemsetmin_display <- itemsetmin

#--------------------------------------------------------------
# HELPERS FOR CASCADING DROPDOWNS
#--------------------------------------------------------------

get_candidates <- function(meta=NULL, rep=NULL, minsup=NULL, gapmin=NULL, gapmax=NULL) {

  cands <- normal_dataset_names

  if (!is.null(meta))
    cands <- cands[startsWith(cands, paste0(meta, "_"))]
  if (!is.null(rep)) {
    if (grepl("motif", rep, ignore.case=TRUE))
      cands <- cands[grepl("motif", cands, ignore.case=TRUE)]
    else
      cands <- cands[endsWith(cands, paste0("_", rep))]
  }
  if (!is.null(minsup))
    cands <- cands[grepl(paste0("_", minsup, "_[^_]+_[^_]+_[^_]+$"), cands, perl=TRUE)]
  if (!is.null(gapmin))
    cands <- cands[grepl(paste0("_[^_]+_", gapmin, "_[^_]+_[^_]+$"), cands, perl=TRUE)]
  if (!is.null(gapmax))
    cands <- cands[grepl(paste0("_[^_]+_[^_]+_", gapmax, "_[^_]+$"), cands, perl=TRUE)]
  cands
}


get_specif_candidates <- function(meta=NULL) {
  cands <- specif_dataset_names
  if (!is.null(meta))
    cands <- cands[startsWith(cands, paste0(meta, "_specifs_"))]
  cands
}

format_specif_choices <- function(cands) {
  if (length(cands) == 0) {
    return(character(0))
  }
  labels <- sub("^([^_]+)_specifs_", "", cands)
  names(cands) <- labels
  cands
}

format_specif_table_for_display <- function(df) {
  as.data.frame(lapply(df, function(col) {
    if (is.numeric(col)) {
      out <- as.character(col)
      out[is.infinite(col) & col > 0] <- "Inf"
      out[is.infinite(col) & col < 0] <- "-Inf"
      return(out)
    }
    col
  }), check.names = FALSE, row.names = rownames(df), stringsAsFactors = FALSE)
}


extract_reps      <- function(cands) unique(ifelse(grepl("motif", cands, ignore.case=TRUE), "motif", sub(".*_([^_]+)$", "\\1", cands)))
extract_minsup    <- function(cands) unique(sub(".*_([^_]+)_[^_]+_[^_]+_[^_]+$", "\\1", cands))
extract_gapmin    <- function(cands) unique(sub(".*_[^_]+_([^_]+)_[^_]+_[^_]+$", "\\1", cands))
extract_gapmax    <- function(cands) unique(sub(".*_[^_]+_[^_]+_([^_]+)_[^_]+$", "\\1", cands))
extract_itemsetmin <- function(cands) unique(sub(".*_[^_]+_[^_]+_[^_]+_([^_]+)$", "\\1", cands))

#--------------------------------------------------------------
# SERVER
#--------------------------------------------------------------
server <- function(input, output, session){


  output$has_specifs_available <- renderText({
    if (has_specifs) "true" else "false"
  })
  outputOptions(output, "has_specifs_available", suspendWhenHidden = FALSE)


# Deal with input selection
  input_selection <- reactive({
    dataset_select <- req(input$dataset_select)           # selecting df all in one
    df_select_concatenated <- req(df_select_concatenated(), cancelOutput = FALSE)   # selecting df by separate categories

     if (input$input_sel_method == FALSE) {
      df <- df_select_concatenated
     } else { 
      df <- dataset_select
     }
    path <- datasets[[df]]   # extract path
    # Ensure it's a single string
    if(!is.character(path) || length(path) != 1){
      stop("Selected dataset is not a valid file path")
    }
    path
  })

  # Load selected data
  data1 <- reactive({
    path <- req(input_selection())
    data <- read.csv(path, sep="\t", row.names = 1, header=T, check.names = FALSE)
  })


  data_CA <- reactive({

    data <- req(data1())
    rownames(data) <- gsub(" ", "_", rownames(data))
    data <- data[rowSums(data) != 0, ]
  })


  data_PCA <- reactive({
    data <- req(data1())
    rownames(data) <- gsub(" ", "_", rownames(data))
    # Observation table from the contingency table: texts (or metadata values)
    # become the individuals (rows), motifs the variables (columns)
    obs <- as.data.frame(t(data), check.names = FALSE)
    # Relative counts: divide each row by the size (nb of tokens) of its text
    # or metadata value, taken from the metadata whose values match the row names
    sizes <- Find(function(s) all(rownames(obs) %in% names(s)), metadata_sizes)
    if (is.null(sizes)) {
      warning("No text/metadata sizes match the rows: PCA uses absolute counts")
      return(obs)
    }
    obs / sizes[rownames(obs)]
  })



  # Reactive value to hold CA result and an error message for display
  ca_res <- reactiveVal(NULL)
  ca_error <- reactiveVal(NULL)
  cluster_error_msg <- reactiveVal(NULL)


  # Selected analysis method (CA or PCA)
  analysis_method <- reactiveVal("CA")
  observeEvent(input$analysis_method, {
    analysis_method(input$analysis_method)
  })


  output$cluster_error_msg_hcpc  <- renderText({ cluster_error_msg() })
  output$cluster_error_msg_parang <- renderText({ cluster_error_msg() })

  # Compute CA automatically when preprocessing result is ready

  observeEvent(data_CA(), {
    d <- data_CA()
    d 

  })

  #Preview data
  output$data_table <- renderDT({

    df <- if (analysis_method() == "PCA") req(data_PCA()) else req(data_CA())
    datatable(
      df,

      options = list(
        pageLength = 10,
        autoWidth = TRUE,
        scrollX = TRUE
      ),
      filter = "top",    # adds per-column filters
      rownames = TRUE
    )
  })


  specif_selection <- reactive({
    req(has_specifs)
    req(input$specifs_metadata_select)
    req(input$specifs_table_select)
    path <- datasets[[input$specifs_table_select]]
    if(!is.character(path) || length(path) != 1){
      stop("Selected specif dataset is not a valid file path")
    }
    path
  })

  specif_data <- reactive({
    path <- req(specif_selection())
    df <- read.csv(path, sep="\t", row.names = 1, header = TRUE, check.names = FALSE)
    format_specif_table_for_display(df)
  })

  output$specifs_table <- renderDT({
    req(has_specifs)
    datatable(
      specif_data(),
      options = list(
        pageLength = 15,
        autoWidth = TRUE,
        scrollX = TRUE
      ),
      filter = "top",
      rownames = TRUE
    )
  })



  # ------------- Screeplot -------------
  # Suffix the default title with the method, without overwriting a custom title
  observeEvent(analysis_method(), {
    defaults <- c("Scree plot", "Scree plot (PCA)", "Scree plot (CA)")
    if (is.null(input$plot_title_scree) || input$plot_title_scree %in% defaults) {
      updateTextInput(session, "plot_title_scree",
        value = paste0("Scree plot (", analysis_method(), ")"))
    }
  })

  # Store the plot as a reactive
  scree_plot <- reactive({
      if (analysis_method() == "PCA"){
        res <- req(res_pca())
        valid_choices <- c("var", "ind")
      } else {
        res <- req(res_ca())
        valid_choices <- c("row", "col")
      }
    p <- fviz_screeplot(res,

      addlabels = TRUE, 
      title=input$plot_title_scree,
      xlab = input$plot_xlab_scree,
      ylab = input$plot_ylab_scree,
      ) + theme_classic()
    p
  })

  # Render the plot
  output$screePlot <- renderPlot({
    p <- req(scree_plot())
    p
  }, res = 96)

  # Download handler
  observeEvent(input$save_scree_plot, {
      #base_dir <- getwd()
      file_name <- paste("CA_plots/ScreePlot_", format(Sys.time(), "%Y-%m-%d_%H-%M-%S"), ".png", sep="")
      full_path <- file.path(patterns_dir, file_name)
      ggsave(full_path, plot = scree_plot(), width = 8, height = 6, dpi = 300)
      showNotification(paste("Plot saved to:", full_path), type = "message")
    }
  )

  # ------------- CA computation -------------
  res_ca <- reactive({

    data <- req(data_CA())                # your reactive data object

    FactoMineR::CA(data, graph = FALSE, ncp = 2)
  })

  # ------------- Prepare data for CA ploting -------------
  ca_prep <- reactive({
    res <- req(res_ca())

    # Extract coordinated for rows and columns
    rows_df <- as.data.frame(res$row$coord[, 1:2])
    cols_df <- as.data.frame(res$col$coord[, 1:2])
    rows_df$label <- rownames(rows_df)
    cols_df$label <- rownames(cols_df)
    # res$row$contrib$label <- rownames(res$row$contrib)
    # res$col$contrib$label <- rownames(res$col$contrib)

    # Subset n-rows for displaying points and labels
    if (input$contrib_threshold) {
  total_contrib_rows <- rowSums(res$row$contrib)
  top_rows <- names(sort(total_contrib_rows, decreasing = TRUE))[1:input$contrib_rows]

  total_contrib_cols <- rowSums(res$col$contrib)
  top_cols <- names(sort(total_contrib_cols, decreasing = TRUE))[1:input$contrib_vars]

  rows_df <- rows_df[rows_df$label %in% top_rows, ]
  cols_df <- cols_df[cols_df$label %in% top_cols, ]
}

    # Also include the raw CA object and contributions if other outputs need them
    list(
      ca = res,
      rows = rows_df,
      cols = cols_df,
      # flags = flags,
      eig = res$eig,
      row_contrib = res$row$contrib,
      col_contrib = res$col$contrib
    )
  })
  
  # ------------- Retrieve axis selection -------------
  observe({
    res <- req(res_ca())
    n_axes <- ncol(res$col$coord)

    updateSelectInput(
      session,
      "selected_axis",
      choices = 1:n_axes,
      selected = 1
    )
  })


  # ------------- Shared CA/PCA plot layers -------------
    # Adds the points, labels and contribution sizes chosen in Plot settings
    # to a base factor map. points_data is the list returned by ca_prep() or pca_prep().
    add_factor_layers <- function(fplot, points_data, plot_title, show_cols = TRUE) {

      cols_df <- points_data$cols
      rows_df <- points_data$rows
      rows_df$contrib_var <- rowSums(
        points_data$row_contrib[rows_df$label, 1:2, drop = FALSE]
      )

      cols_df$contrib_var <- rowSums(
        points_data$col_contrib[cols_df$label, 1:2, drop = FALSE]
      )

      contribution_title <- "Contribution (axes 1 + 2)"


      # Retrieve display properties choices

        # show_cols = FALSE drops column layers whatever the checkboxes say
        show_col_points <- show_cols && "Columns points" %in% input$show_items
        show_row_points <- "Rows points" %in% input$show_items
        show_col_labels <- show_cols && "Columns labels" %in% input$show_items

        show_row_labels <- "Rows labels" %in% input$show_items
        points_size <- "Points size" %in% input$size
        label_size <- "Label size" %in% input$size
        # points_color <- "Points color" %in% input$size
        # label_color <- "Label color" %in% input$size
          

		fplot <- fplot +
  scale_size_continuous(range = c(2, 6))									#minimal size for readability (HugoDumoulin)
      # Conditionnaly add points and/or labels
      strenght <- input$jitter_strength
      if (show_col_labels) {                                                      # If labels of rows are showed   
        if (label_size) {                                                    # If label size == contrib
          fplot <- fplot +
          geom_text_repel(data = cols_df,
                aes(x = `Dim 1`, y = `Dim 2`, label = label,
                size = contrib_var),
                color = "red", vjust = -0.5,
                force=strenght) #+
                # guides(size="none")
        } else {                                                               # If not, label size is fixed
          fplot <- fplot +
          geom_text_repel(data = cols_df,
                aes(x = `Dim 1`, y = `Dim 2`, label = label),
                color = "red", vjust = -0.5,
                force=strenght)
        }
      }
      if (show_row_labels) {                                                      # If labels of rows are showed
        if (label_size) {                                                    # If label size == contrib and jitter                                                      # If label size == contrib
          fplot <- fplot +
          geom_text_repel(data = rows_df,
                aes(x = `Dim 1`, y = `Dim 2`, label = gsub("dep_|lemma_|pos_|feats_", "", label),
                size = contrib_var),
                color = "blue", vjust = -0.5,
                force=strenght) #+
                # guides(size="none")
        } else {
                fplot <- fplot +
          geom_text_repel(data = rows_df,
                aes(x = `Dim 1`, y = `Dim 2`, label = gsub("dep_|lemma_|pos_|feats_", "", label)),
                color = "blue", vjust = -0.5,
                force=strenght)
        }
      }
      if (show_col_points) {                                                      # If points of columns are showed
        if (points_size) {                                                          # If points size == contrib
          fplot <- fplot +
          geom_point(data = cols_df,
                aes(x = `Dim 1`, y = `Dim 2`, size = contrib_var), shape = 17,
                color = "red") +
                labs(size = contribution_title)
        } else {                                                                    # If not, points size is fixed
          fplot <- fplot +
          geom_point(data = cols_df,
                aes(x = `Dim 1`, y = `Dim 2`), shape = 17,
                color = "red")
        }
      }
      if (show_row_points) {                                                        # If points of rows are showed
        if (points_size) {                                                            # If points size == contrib
          fplot <- fplot +
          geom_point(data = rows_df,
                aes(x = `Dim 1`, y = `Dim 2`, size = contrib_var), shape = 19,
                color = "blue")
        } else {                                                                     # If not, points size is fixed
          fplot <- fplot +
          geom_point(data = rows_df,
                aes(x = `Dim 1`, y = `Dim 2`), shape = 19,
                color = "blue")
        }
      }

      # Conditional for point size legend but no label size legend
      if (points_size & !label_size) {
        fplot <- fplot + guides(size = guide_legend(title = contribution_title))
      } else if (!points_size) {
        fplot <- fplot + guides(size = "none")
      } else if (points_size & label_size) {
        fplot <- fplot + guides(size = guide_legend(
          title = contribution_title,
          override.aes = list(label = "")))
      # } else if (points_size & input$deactivate_jitter & !label_size) {
      #   fplot <- fplot + guides(size = guide_legend(
      #     title = contribution_title,
      #     override.aes = list(label = "")))
      } else {
        fplot <- fplot
      }

      fplot <- fplot +
        labs(title = plot_title)

      fplot
    }

  # ------------- PCA computation -------------
  res_pca <- reactive({
    data <- req(data_PCA())
    FactoMineR::PCA(data, graph = FALSE, ncp = 2, scale.unit=TRUE)
  })

  # ------------- Prepare data for PCA ploting -------------
  # Rows are the PCA individuals, columns the PCA variables, so the same
  # Rows/Columns settings apply as for CA
  pca_prep <- reactive({
    res <- req(res_pca())

    ind_coord <- res$ind$coord[, 1:2]
    var_coord <- res$var$coord[, 1:2]
    # Variable coordinates are correlations (within [-1, 1]): stretch them
    # onto the individuals' scale so both fit on one biplot (as fviz_pca_biplot does)
    r <- 0.7 * min(diff(range(ind_coord[, 1])) / diff(range(var_coord[, 1])),
                   diff(range(ind_coord[, 2])) / diff(range(var_coord[, 2])))
    var_coord <- var_coord * r

    # FactoMineR::PCA names axes "Dim.1", CA names them "Dim 1": align on CA
    to_ca_names <- function(m) { colnames(m) <- sub("Dim.", "Dim ", colnames(m), fixed = TRUE); m }
    rows_df <- as.data.frame(to_ca_names(ind_coord))
    cols_df <- as.data.frame(to_ca_names(var_coord))
    rows_df$label <- rownames(rows_df)
    cols_df$label <- rownames(cols_df)
    row_contrib <- to_ca_names(res$ind$contrib)
    col_contrib <- to_ca_names(res$var$contrib)

    # Subset n-rows for displaying points and labels
    if (input$contrib_threshold) {
      top_rows <- names(sort(rowSums(row_contrib), decreasing = TRUE))[1:input$contrib_rows]
      top_cols <- names(sort(rowSums(col_contrib), decreasing = TRUE))[1:input$contrib_vars]
      rows_df <- rows_df[rows_df$label %in% top_rows, ]
      cols_df <- cols_df[cols_df$label %in% top_cols, ]
    }

    list(
      pca = res,
      rows = rows_df,
      cols = cols_df,
      eig = res$eig,
      row_contrib = row_contrib,
      col_contrib = col_contrib
    )
  })

  # ------------- PCA ploting ------------
    # Store the plot as a reactive
    PCA__plot <- reactive({
      res <- req(res_pca())
      points_data <- req(pca_prep())

      pca_plot <- factoextra::fviz_pca_ind(res, geom.ind = "none", geom.var = "none",
                                              ggtheme = ggplot2::theme_minimal())

      # Rows only: columns (variables) are drawn in the circle plot
      add_factor_layers(pca_plot, points_data, input$plot_title_PCA, show_cols = FALSE)
    })

    # Circle plot
        PCA_circle_plot <- reactive({
      res <- req(res_pca())

      # Coordonnées de corrélation du cercle des variables
      vars <- data.frame(
        x = res$var$coord[, 1],
        y = res$var$coord[, 2],
        label = rownames(res$var$coord),
        contrib_var = rowSums(
          res$var$contrib[, 1:2, drop = FALSE]
        )
      )

      vars$display_label <- gsub(
        "dep_|lemma_|pos_|feats_", "", vars$label
      )

      # Filtrer les variables les plus contributives
      if (isTRUE(input$contrib_threshold)) {
        n <- req(input$contrib_vars)
        keep <- head(order(vars$contrib_var, decreasing = TRUE), n)
        vars <- vars[keep, , drop = FALSE]
      }

      show_points <- "Columns points" %in% input$show_items
      show_labels <- "Columns labels" %in% input$show_items
      points_size <- "Points size" %in% input$size
      label_size <- "Label size" %in% input$size

      # Fond : cercle et axes
      p <- factoextra::fviz_pca_var(
        res,
        geom.var = "none",
        ggtheme = ggplot2::theme_minimal()
      )

      # Flèches et points aux extrémités
      if (show_points) {
        p <- p + geom_segment(
          data = vars,
          aes(x = 0, y = 0, xend = x, yend = y),
          arrow = grid::arrow(length = grid::unit(0.2, "cm")),
          color = "red",
          alpha = 0.6,
          inherit.aes = FALSE
        )

        point_mapping <- aes(x = x, y = y)
        if (points_size) {
          point_mapping$size <- aes(size = contrib_var)$size
        }

        p <- p + geom_point(
          data = vars,
          mapping = point_mapping,
          color = "red",
          shape = 17,
          inherit.aes = FALSE
        )
      }

      # Étiquettes, avec taille et répulsion réglables
      if (show_labels) {
        label_mapping <- aes(
          x = x, y = y, label = display_label
        )
        if (label_size) {
          label_mapping$size <- aes(size = contrib_var)$size
        }

        p <- p + ggrepel::geom_text_repel(
          data = vars,
          mapping = label_mapping,
          color = "red",
          force = input$jitter_strength,
          box.padding = 0.25 + 1.5 * input$jitter_strength,
          seed = 42,
          show.legend = FALSE,
          inherit.aes = FALSE
        )
      }

      p <- p + scale_size_continuous(
        name = "Contribution (axes 1 + 2)",
        range = c(2, 6)
      )

      if (!show_points || !points_size) {
        p <- p + guides(size = "none")
      }

      p + labs(title = input$plot_title_PCA_circle)
    })
    
    # Display it
    output$PCAplot <- renderPlot({
      p <- req(PCA__plot())
      p
    }, res = 96)
    output$PCAcircleplot <- renderPlot({
      p <- req(PCA_circle_plot())
      p
    }, res = 96)

  # ------------- CA ploting -------------
    # Store the plot as a reactive
      CA__plot <- reactive({
      res <- req(res_ca())
      points_data <- req(ca_prep())

      ca_plot <- factoextra::fviz_ca_biplot(
        res,
        geom = "none",
        ggtheme = ggplot2::theme_minimal()
      )

      add_factor_layers(ca_plot, points_data, input$plot_title_CA)
    })
    
    
    # Display it
    output$CAplot <- renderPlot({
      p <- req(CA__plot())
      p
    }, res = 96)


    # Download handler (saves the plot(s) of the selected analysis method)
    # PCA: individuals and circle plots are saved as two separate files
    observeEvent(input$save_CA_plot, {
        method <- analysis_method()
        plots <- if (method == "PCA") {
          list(PCA_individuals = PCA__plot(), PCA_circle = PCA_circle_plot())
        } else {
          list(CA = CA__plot())
        }
        #base_dir <- getwd()
        timestamp <- format(Sys.time(), "%Y-%m-%d_%H-%M-%S")
        for (name in names(plots)) {
          file_name <- paste("CA_plots/", name, "_", timestamp, ".png", sep="")
          full_path <- file.path(patterns_dir, file_name)
          ggsave(full_path, plot = plots[[name]], width = 12, height = 9, dpi = 300)
          showNotification(paste("Plot saved to:", full_path), type = "message")
        }

      }
    )

  # ------------- Contrib plotting -------------

  # Dimension choices depend on the method: row/col for CA, var/ind for PCA
  observeEvent(analysis_method(), {
    choices <- if (analysis_method() == "PCA") c("var", "ind") else c("row", "col")
    updateSelectInput(session, "contrib_choice", choices = choices, selected = choices[1])

    # Suffix the default title with the method, without overwriting a custom title
    base_title <- "Contribution of XX to Dim-XX"
    defaults <- c(base_title, paste0(base_title, c(" (PCA)", " (CA)")))
    if (is.null(input$plot_title_contrib) || input$plot_title_contrib %in% defaults) {
      updateTextInput(session, "plot_title_contrib",
        value = paste0(base_title, " (", analysis_method(), ")"))
    }
  })

  contrib_plot <- reactive({
    if (analysis_method() == "PCA"){
        res <- req(res_pca())
        valid_choices <- c("var", "ind")
      } else {
        res <- req(res_ca())
        valid_choices <- c("row", "col")
      }
    # Get user inputs
      user_choice <- req(input$contrib_choice)  # e.g. "row"/"col" (CA) or "var"/"ind" (PCA)
      # Wait for the selector to update after a method switch
      req(user_choice %in% valid_choices)

      user_axes   <- req(input$contrib_axes)    # e.g. 1 or 2
    if (input$contrib_custom_title) {
      plot_obj <- fviz_contrib(res,
        choice = user_choice,
        axes = user_axes,
        title = input$plot_title_contrib)
      plot_obj
    } else {
      plot_obj <- fviz_contrib(res,
        choice = user_choice,
        axes = user_axes)

      # Suffix the default factoextra title with the method
      plot_obj <- plot_obj +
        ggtitle(paste0(plot_obj$labels$title, " (", analysis_method(), ")"))
      plot_obj
    }

    if (input$scree_hide_labels) {
      plot_obj <- plot_obj +
        theme(axis.text.x = element_blank(),
              axis.ticks.x = element_blank())
    }

    plot_obj <- plot_obj +
    ylab(input$plot_ylab_contrib)
  })

  output$contribPlot <- renderPlot({
      p <- req(contrib_plot())
      p
    }, res = 96)

  # Download handler
  observeEvent(input$save_contrib_plot, {
      #base_dir <- getwd()
      file_name <- paste("CA_plots/Contrib_", format(Sys.time(), "%Y-%m-%d_%H-%M-%S"), ".png", sep="")
      full_path <- file.path(patterns_dir, file_name)
      ggsave(full_path, plot = contrib_plot(), width = 8, height = 6, dpi = 300)
      showNotification(paste("Plot saved to:", full_path), type = "message")
    }
  )



  # ------------- Clustering -------------
  # Note : because HCPC is base R (not ggplot), I can't create it in a reactive and then renderPlot and save it through observeEvent
  # Simplest fix is to copy-paste the code in two functions

  # HCPC's cluster.CA only applies to CA: PCA always clusters rows (individuals)
  cluster_row_or_col <- reactive({
    if (analysis_method() == "PCA") "rows" else req(input$cluster_row_or_col)
  })

  output$clusters_plot <- renderPlot({
    req(input$nb_clusters,

      !is.null(input$type_of_plot),
      !is.null(input$ind_name),
      !is.null(input$bool_consol_tree),
      !is.null(input$bool_draw_tree)
    )

      # Select PCA of CA
      res <- if (analysis_method() == "PCA") req(res_pca()) else req(res_ca())
    nb_clusters <- ifelse(input$enable_num_clusters, input$nb_clusters, -1)
    type <- input$type_of_plot
    ind_name <- if (isTRUE(input$ind_name)) "FALSE" else "TRUE"
    draw_tree <- if (isTRUE(input$bool_draw_tree)) "TRUE" else "FALSE"

    tryCatch({

      hclust <- FactoMineR::HCPC(res,
        nb.clust = nb_clusters,
        consol = input$bool_consol_tree,
        graph = FALSE,
        cluster.CA = cluster_row_or_col())


      nb_clusters_after_HCPC <- length(unique(hclust$data.clust$clust))
      palette(scales::hue_pal()(nb_clusters_after_HCPC))

      plot.HCPC(hclust,
        choice = type,
        ind.names = ind_name,
        draw.tree = draw_tree)
    }, error = function(e) {
      if (grepl("arguments must have same length", conditionMessage(e), fixed = TRUE))
        cluster_error_msg("Clustering failed: the number of items is incompatible with the requested number of clusters. Try changing the number of clusters or the row/column setting.")
      stop(e)
    })
  }, res = 96)

  #Download handler
  observeEvent(input$download_clusters, {
    req(input$nb_clusters, !is.null(input$type_of_plot), !is.null(input$ind_name))
    res <- if (analysis_method() == "PCA") req(res_pca()) else req(res_ca())
    nb_clusters <- ifelse(input$enable_num_clusters, input$nb_clusters, -1)
    type <- input$type_of_plot
    ind_name <- if (isTRUE(input$ind_name)) "FALSE" else "TRUE"
    hclust <- HCPC(res,
      nb.clust = nb_clusters,
      consol = input$bool_consol_tree,
      graph = FALSE,
      cluster.CA = cluster_row_or_col())


    #base_dir <- getwd()
    full_dir <- ca_plots_dir
    if (!dir.exists(full_dir)) dir.create(full_dir, recursive = TRUE)
    full_path <- file.path(full_dir, paste0("Clusters_", format(Sys.time(), "%Y-%m-%d_%H-%M-%S"), ".png"))

    png(full_path, width = 12, height = 9, units="in", res=300)
    plot.HCPC(hclust, choice = type, ind.names = ind_name)
    dev.off()

    showNotification(paste("Plot saved to:", full_path), type = "message")
  })

  # Disable cluster numbering and activate on checkbox
  disable("nb_clusters")
  observeEvent(input$enable_num_clusters, {
    if (input$enable_num_clusters) {
      enable("nb_clusters")
    } else {
      disable("nb_clusters")
    }
  })

  # Diable scaled jittering if no scaling labels on CA
  # disable("deactivate_jitter")
  # observeEvent(input$size, {
  #   # label_size <- "Label size" %in% input$size
  #   if ("Label size" %in% input$size) {
  #     enable("deactivate_jitter")
  #   } else {
  #     disable("deactivate_jitter")
  #     updateCheckboxInput(session, "deactivate_jitter", value = FALSE)
  #   }
  # }, ignoreNULL = FALSE)

  # ------------- Parangons, dist, v-test -------------

  plot_CA_clusters <- reactive({

    req(input$parang_paraORdist, input$nb_clusters)
    tryCatch({
    cluster_error_msg(NULL)
    data_type <- cluster_row_or_col()

      if (data_type == "columns") {
        data_type <- "col"
      } else {
        data_type <- "row"
      }
    individus_type <- input$parang_paraORdist
      if (individus_type == "closest to the center (medoids)") {
        individus_type <- "para"
        v_test_bool <- FALSE
      } else if (individus_type == "farthest from other clusters") {
        individus_type <- "dist"
        v_test_bool <- FALSE
      } else {
        individus_type <- "para"
        v_test_bool <- TRUE
      }

    nb_clusters <- ifelse(input$enable_num_clusters, input$nb_clusters, -1)


    
      # Select PCA of CA
      res <- if (analysis_method() == "PCA") req(res_pca()) else req(res_ca())

    # Recreate HCPC df
    # hclust <- HCPC(res, nb.clust = nb_clusters, graph = FALSE, cluster.CA = input$cluster_row_or_col)
    hclust_row <- HCPC(res, nb.clust = nb_clusters, graph=F, nb.par = input$nb_modalites_vtest)
    # Column clustering only exists for CA
    if (analysis_method() == "CA") {
      hclust_col <- HCPC(res, cluster.CA="columns", nb.clust = nb_clusters, graph=F, nb.par = input$nb_modalites_vtest)
    }

    hclust <- if (data_type == "col") hclust_col else hclust_row

    # Coordinates of the clustered items and of the describing variables
    # CA: row/col (the describing side is the other one); PCA: ind/var
    if (analysis_method() == "PCA") {
      ind_coords <- res$ind$coord
      var_coords <- res$var$coord
      desc_var <- hclust$desc.var$quanti
    } else {
      other_type <- if (data_type == "col") "row" else "col"
      ind_coords <- res[[data_type]]$coord
      var_coords <- res[[other_type]]$coord
      desc_var <- hclust$desc.var
    }

    # Extraire les parangons
    individus <- hclust$desc.ind[[individus_type]]
    individus.names <- unlist(lapply(individus, names))

    # Coordonnées des parangons sur les deux premières dimensions
    coords.individus <- ind_coords[individus.names, 1:2]

    
    # Déterminer à quel cluster appartient chaque parangon
    clusters <- sapply(individus.names, function(x) {
      which(sapply(individus, function(cl) x %in% names(cl)))
    })
    clusters <- factor(clusters)
    
    # Construire le data.frame
    df <- data.frame(
      Dim1 = coords.individus[,1],
      Dim2 = coords.individus[,2],
      Cluster = clusters,
      Nom = individus.names
    )
    
    if (isTRUE(v_test_bool)) {

      # type_array <- paste0("hclust_",data_type,"$desc.var")
      # array_type <- eval(parse(text = type_array))
      
      #extraire pour chaque cluster les var où v.test > 0
      # clust <- lapply(array_type, function(mat) {

      #extraire pour chaque cluster les var où v.test > 0
      clust <- lapply(desc_var, function(mat) {
        # PCA: clusters with no significant variable are NULL
        if (is.null(mat)) return(character(0))

        # Sélectionner uniquement les lignes avec v.test > 0
        vars <- rownames(mat)[mat[, "v.test"] > 0]
        # Garder au plus 5 variables
        head(vars, input$nb_modalites_vtest)
      })

      clust_clean <- lapply(clust, function(vec) {
          # Remplacer uniquement les points entre deux blocs {lemma_"..."} -> {lemma_"..."} {lemma_"..."}
        gsub("\\}\\.\\{", "} {", vec)
        })

        ind = unlist(clust_clean)


      #récupérer les coordonnées de ces ind
      coords.individus <- var_coords[ind, 1:2, drop = FALSE]


      clusters <- unlist(lapply(names(clust_clean), function(cluster_name) {
      individus <- clust_clean[[cluster_name]]
        setNames(rep(cluster_name, length(individus)), individus)
      }))
      clusters <- factor(clusters)

      # Construire le data.frame
      df <- data.frame(
        Dim1 = coords.individus[,1],
        Dim2 = coords.individus[,2],
        Cluster = clusters,
        Nom = ind
      )

      p <- ggplot(data = df, aes(x = Dim1, y = Dim2, color = Cluster)) +
        geom_point(size = 3) +
        ggrepel::geom_text_repel(aes(label = Nom), show.legend = FALSE, size = 3) +
        geom_hline(yintercept = 0, linetype = "dashed", color = "grey70") +
        geom_vline(xintercept = 0, linetype = "dashed", color = "grey70") +
        theme_classic() +
        theme(
          panel.grid = element_blank(),
          axis.line = element_blank(),
          axis.ticks = element_blank(),
          axis.text = element_blank(),
          axis.title = element_text(color = "grey30")
        ) +
        labs(
          title = input$plot_title_parang,
          x = input$plot_xlab_parang,
          y = input$plot_ylab_parang
        )
      
      # test_full <- paste0("hclust_", data_type, "$call$t$nb.clust")
      # test <- eval(parse(text = test_full))

    } else {

    # Construire le graphique
    p <- ggplot(data = df, aes(x = Dim1, y = Dim2, color = Cluster)) +
      geom_point(size = 3) +
      ggrepel::geom_text_repel(aes(label = Nom), show.legend = FALSE, size = 3) +
      geom_hline(yintercept = 0, linetype = "dashed", color = "grey70") +
      geom_vline(xintercept = 0, linetype = "dashed", color = "grey70") +
      theme_classic() +
      theme(
        panel.grid = element_blank(),
        axis.line = element_blank(),
        axis.ticks = element_blank(),
        axis.text = element_blank(),
        axis.title = element_text(color = "grey30")
      ) +
      labs(
        title = input$plot_title_parang,
        x = input$plot_xlab_parang,
        y = input$plot_ylab_parang
      )
    }

    return(p)
    }, error = function(e) {
      if (grepl("arguments must have same length", conditionMessage(e), fixed = TRUE))
        cluster_error_msg("Clustering failed: the number of items is incompatible with the requested number of clusters. Try changing the number of clusters or the row/column setting.")
      stop(e)
    })
  })


    # Display it (one output per representatives tab; only the visible one renders)
    for (out_id in c("CA_clusters_plot_medoids", "CA_clusters_plot_dist", "CA_clusters_plot_vtest")) {
      output[[out_id]] <- renderPlot({
        p <- req(plot_CA_clusters())
        p
      }, res = 96)
    }


    # Download handler
    observeEvent(input$save_cluster_v_test_post, {
        #base_dir <- getwd()
        file_name <- paste("CA_plots/Cluster_by_points", format(Sys.time(), "%Y-%m-%d_%H-%M-%S"), ".png", sep="")
        full_path <- file.path(patterns_dir, file_name)
        ggsave(full_path, plot = plot_CA_clusters(), width = 12, height = 9, dpi = 300)
        showNotification(paste("Plot saved to:", full_path), type = "message")
      }
    )

  # UI Stuff
  observe({
    # Conditional logic to change textInput default value

    req(input$parang_paraORdist)
    if (input$parang_paraORdist == "closest to the center (medoids)") {
      updateTextInput(session, "plot_title_parang", value = "Factor map - medoids")
    } else if (input$parang_paraORdist == "farthest from other clusters") {
      updateTextInput(session, "plot_title_parang", value = "Factor map - representatives farthest from other clusters")
    } else if (input$parang_paraORdist == "variable associated by v-test") {
      updateTextInput(session, "plot_title_parang", value = "Factor map - variables associated by v-test")

    }
  })

# ------------- Cascading dropdown updates -------------

  observeEvent(input$dataset_select_metadata, {
    cands <- get_candidates(meta=input$dataset_select_metadata)
    reps <- extract_reps(cands)
    updateSelectInput(session, "dataset_select_representation", choices=reps, selected=reps[1])
  }, ignoreInit=TRUE)

  observeEvent(input$dataset_select_representation, {
    meta <- input$dataset_select_metadata
    rep  <- input$dataset_select_representation
    if (grepl("motif", rep, ignore.case=TRUE)) {
      vals <- extract_minsup(get_candidates(meta=meta, rep=rep))
      updateSelectInput(session, "dataset_select_minsup", choices=vals, selected=vals[1])
    }
  }, ignoreInit=TRUE)

  observeEvent(input$dataset_select_minsup, {
    if (!grepl("motif", input$dataset_select_representation, ignore.case=TRUE)) return()
    cands <- get_candidates(meta=input$dataset_select_metadata, rep=input$dataset_select_representation, minsup=input$dataset_select_minsup)
    vals <- extract_gapmin(cands)
    updateSelectInput(session, "dataset_select_gapmin", choices=vals, selected=vals[1])
  }, ignoreInit=TRUE)

  observeEvent(input$dataset_select_gapmin, {
    if (!grepl("motif", input$dataset_select_representation, ignore.case=TRUE)) return()
    cands <- get_candidates(meta=input$dataset_select_metadata, rep=input$dataset_select_representation, minsup=input$dataset_select_minsup, gapmin=input$dataset_select_gapmin)
    vals <- extract_gapmax(cands)
    updateSelectInput(session, "dataset_select_gapmax", choices=vals, selected=vals[1])
  }, ignoreInit=TRUE)

  observeEvent(input$dataset_select_gapmax, {
    if (!grepl("motif", input$dataset_select_representation, ignore.case=TRUE)) return()
    cands <- get_candidates(meta=input$dataset_select_metadata, rep=input$dataset_select_representation, minsup=input$dataset_select_minsup, gapmin=input$dataset_select_gapmin, gapmax=input$dataset_select_gapmax)
    vals <- extract_itemsetmin(cands)
    updateSelectInput(session, "dataset_select_itemsetmin", choices=vals, selected=vals[1])
  }, ignoreInit=TRUE)


  observe({
    req(has_specifs)
    meta <- req(input$specifs_metadata_select)
    cands <- get_specif_candidates(meta)
    selected <- if (length(cands) > 0) cands[1] else character(0)
    updateSelectInput(session, "specifs_table_select", choices = format_specif_choices(cands), selected = selected)
  })


df_select_concatenated <- reactive({
  metadata_select <- req(input$dataset_select_metadata)
  representation_select <- req(input$dataset_select_representation)

  if (grepl("motif", representation_select, ignore.case = TRUE)) {
    minsup_select        <- as.character(req(input$dataset_select_minsup))
    gapmin_select        <- as.character(req(input$dataset_select_gapmin))
    gapmax_select        <- as.character(req(input$dataset_select_gapmax))
    itemsetmin_select    <- as.character(req(input$dataset_select_itemsetmin))

    suffix <- paste(minsup_select, gapmin_select, gapmax_select, itemsetmin_select, sep = "_")


    candidates <- normal_dataset_names

    candidates <- candidates[startsWith(candidates, paste0(metadata_select, "_"))]
    candidates <- candidates[grepl("motif", candidates, ignore.case = TRUE)]
    candidates <- candidates[endsWith(candidates, suffix)]

    df <- candidates[1]
  } else {
    df <- paste(metadata_select, representation_select, sep = "_")
  }

  df
})

observe({
  # print("test:")
  print("Concatenated:")
  print(df_select_concatenated())
  print("Single string:")
  print(input$dataset_select)
  # print(datasets)
})

}


#--------------------------------------------------------------
# UI
#--------------------------------------------------------------
ui <- page_navbar(
  tags$head(
    tags$style(HTML("
      /* Make dropdown options wrap long words */
      .selectize-dropdown .option {
        white-space: normal !important;
        overflow-wrap: anywhere !important;
        word-break: break-all !important;
      }

      /* Wrap the selected item inside input */
      .selectize-input > div {
        white-space: normal !important;
        overflow-wrap: anywhere !important;
        word-break: break-all !important;
      }

      /* Let the dropdown expand wider */
      .selectize-dropdown {
        width: auto !important;
        min-width: 400px;
        max-width: 800px;
      }

      /* Notifications wide enough for full file paths */
      #shiny-notification-panel {
        max-width: calc(100vw - 20px);
        right: 10px;
        width: 600px;
      }
      .shiny-notification {
        width: 100%;
        word-break: break-all;
      }
    "))
  ),
  useShinyjs(),
  title = "MWB: Motif Work Bench",
  id = "tabselected",
  # tags$div(style = "text-align: left; color: #888; font-size: 18px; margin-bottom: 10px;",
  #   "User interface for Correspondence Analysis and clustering"
  # ),
  # tags$div(style = "text-align: left; color: #888; font-size: 12px; margin-bottom: 10px;",
  #   "Timothée Premat and Hugo Dumoulin, ArchivU project, 2025"
  # ),

  sidebar = accordion(
    id = "accordions",
    open = "Plot settings",
        accordion_panel(
          title = "Motifs settings ",
          id = "data_settings_accordion",
          conditionalPanel(
            condition = "input.input_sel_method == true",
              selectInput(
                inputId = "dataset_select",          # ID for server to access
                label = tooltip(
                    trigger = list(
                      "Dataset",
                      bs_icon("info-circle")
                    ),
                    HTML("DATASET SELECTION<br/>
                    Depending on your settings, MWB produced several datasets. Select the one to be plotted.")
                  ),

                choices = normal_dataset_names,            # populate dropdown with keys
                selected = normal_dataset_names[1]

              ),
          ),
          conditionalPanel(
            condition = "input.input_sel_method == false",
              selectInput(
                inputId = "dataset_select_metadata",
                label = tooltip(
                    trigger = list(
                      "Metadata",
                      bs_icon("info-circle")
                    ),
                    HTML("DATASET SELECTION<br/>
                    Depending on your settings, MWB produced several datasets. Select the contrastive metadata.")
                  ),
                choices = metadata_name,            # populate dropdown with keys
                selected = metadata_name[1]
              ),
              selectInput(
                inputId = "dataset_select_representation",
                label = tooltip(
                    trigger = list(
                      "Level of representation",
                      bs_icon("info-circle")
                    ),
                    "Select the level of representation used to define linguistic units."
                  ),
                choices = pattern_representation,            # populate dropdown with keys
                selected = pattern_representation[1]
              ),
              conditionalPanel(condition = "input.dataset_select_representation == 'motif' || input.dataset_select_representation == 'motifs' || input.dataset_select_representation == 'internal-clustering-motifs'",
                selectInput(
                  inputId = "dataset_select_minsup",
                  label = tooltip(
                    trigger = list(
                      "Minsup",
                      bs_icon("info-circle")
                    ),
                    "Select the minimal support frequency for motifs."
                  ),
                  choices = minsup_display,            # populate dropdown with keys
                  selected = minsup_display[1]
                ),
                selectInput(
                  inputId = "dataset_select_gapmin",
                  label = tooltip(
                    trigger = list(
                      "Gapmin",
                      bs_icon("info-circle")
                    ),
                    "Select the gap requirement for motifs."
                  ),
                  choices = gapmin_display,            # populate dropdown with keys
                  selected = gapmin_display[1]
                ),
                selectInput(
                  inputId = "dataset_select_gapmax",
                  label = tooltip(
                    trigger = list(
                      "Gapmax",
                      bs_icon("info-circle")
                    ),
                    "Select gap tolerance for motifs."
                  ),
                  choices = gapmax_display,            # populate dropdown with keys
                  selected = gapmax_display[1]
                ),
                selectInput(
                  inputId = "dataset_select_itemsetmin",
                  label = tooltip(
                    trigger = list(
                      "Itemset min size",
                      bs_icon("info-circle")
                    ),
                    "Select the minimal size of motifs (nbr of itemsets)."
                  ),
                  choices = itemsetmin_display,            # populate dropdown with keys
                  selected = itemsetmin_display[1]
                ),
              ),
            ),
          checkboxInput("input_sel_method", " Use single name", value=FALSE)
        ),
        accordion_panel("Plot settings",
          id = "plot_settings_accordion",

          selectInput(
            inputId = "analysis_method",
            label = tooltip(
              trigger = list(
                "Analysis method",
                bs_icon("info-circle")
              ),
              HTML("PCA: Principal Component Analysis<br/>CA: Correspondence Analysis<br/>Note that
              due to multidimensionality of motives, CA can be misleading in some cases.")
            ),
            choices = c("PCA" = "PCA", "CA" = "CA"),
            selected = "PCA"
          ),
          conditionalPanel(condition = "input.tabselected == 'PCA-CA'",
            checkboxInput("contrib_threshold", "Min. contrib. threshold", value=TRUE),

              conditionalPanel(
                condition = "input.contrib_threshold == true",
                sliderInput(
                  "contrib_vars",

                  label = HTML("<i>N</i>-th most contrib. cols"),

                  min = 1,
                  max = 100,
                  value = 10,
                  step = 5
                ),
                sliderInput(
                  "contrib_rows",

                  label = HTML("<i>N</i>-th most contrib. rows"),
                  min = 1,
                  max = 100,
                  value = 10,
                  step = 5
                ),
              ),
            checkboxGroupInput(
              inputId = "show_items",
              label = "Show:",
              choices = c("Columns points", "Columns labels", "Rows points", "Rows labels"),
              selected = c("Columns points", "Columns labels", "Rows points", "Rows labels")
            ),
            checkboxGroupInput(
              inputId = "size",
              label = "Show contribution as:",
              choices = c("Points size", "Label size")#,
              # selected = "none")
            ),
            #conditionalPanel(
             # condition = "input.size == 'Points size' || input.size == 'Label size'",
             # selectInput(
             #   "selected_axis",
             #   "Axis for contribution",
             #   choices = NULL,  # initially empty
             #  selected = 1
             # ),
         	#   ),
            sliderInput(
              "jitter_strength",
              "Strenght of label repelling:",
              min = 0,
              max = 1,
              value = 0.5,
              step = 0.05
            ),
            # p(HTML("<i>Scaling labels often results in lesser constributive labels disapearing. You might need to deactivate jittering if lines are displayed with no labels:</i>")),
            # checkboxInput("deactivate_jitter", HTML("Deactivate jittering <i>(only available with 'Label size' checked)</i>"), value=FALSE),

            conditionalPanel(condition = "input.analysis_method == 'CA'",
              textInput("plot_title_CA", "Plot Title:", value = "CA - Biplot")
            ),
            conditionalPanel(condition = "input.analysis_method == 'PCA'",
              textInput("plot_title_PCA", "Individuals plot title:", value = "PCA - Individuals"),
              textInput("plot_title_PCA_circle", "Circle plot title:", value = "PCA - Variables")
            ),

            actionButton(
                  inputId = "save_CA_plot",
                  label = "Save plot",
                  icon = icon("download"), # FontAwesome icon before text, as in downloadButton
                  class = "btn-primary", # Optional: Bootstrap color styling
                  style = "width: 100%;"
                )
          ),
          conditionalPanel(
            condition="input.tabselected == 'scree'",
              textInput("plot_title_scree", "Plot title", value = "Scree plot"),
              textInput("plot_ylab_scree", "Y axis title", value = "Percentage of explained variances"),
              textInput("plot_xlab_scree", "X axis title:", value = "Dimensions"),
              actionButton(
                inputId = "save_scree_plot",
                label = "Save plot",
                icon = icon("download"), # FontAwesome icon before text, as in downloadButton
                class = "btn-primary", # Optional: Bootstrap color styling
                style = "width: 100%;"
              ),
          ),
          conditionalPanel(
            condition="input.tabselected == 'contrib'",
              selectInput(
                "contrib_choice",
                "Select dimension:",
                choices = c("row", "col"),
                selected = "row"
              ),
              numericInput(
                "contrib_axes",
                "Select axis:",
                value = 1,
                min = 1,
                max = 5
              ),
              checkboxInput("contrib_custom_title", "Use custom title?", value=FALSE),
                conditionalPanel(
                  condition = "input.contrib_custom_title == true",
                  textInput("plot_title_contrib", "Plot Title:", value = "Contribution of XX to Dim-XX"),
                ),              
              textInput("plot_ylab_contrib", "Y axis title", value = "Contributions (%)"),
              checkboxInput("scree_hide_labels", "Hide labels", value=FALSE),
              actionButton(
                inputId = "save_contrib_plot",
                label = "Save plot",
                icon = icon("download"), # FontAwesome icon before text, as in downloadButton
                class = "btn-primary", # Optional: Bootstrap color styling
                style = "width: 100%;"
              )
          ),
          conditionalPanel(
            condition="input.tabselected == 'clustering' || input.tabselected == 'parang_panel'",
              checkboxInput(
                "enable_num_clusters",
                "Use custom number of clusters",
                value = FALSE
              ),
              numericInput(
                "nb_clusters",
                "Custom number of clusters:",
                min = 2,
                value = 2
              ),

              # Row/column clustering only applies to CA (PCA always clusters rows)
              conditionalPanel(
                condition = "input.analysis_method == 'CA'",
                selectInput(
                  "cluster_row_or_col",
                  "Select dimension:",
                  choices = c("rows", "columns"),
                  selected = "rows"
                )
              ),
              hr()
          ),
          conditionalPanel(
            condition="input.tabselected == 'clustering'",
              selectInput(
                "type_of_plot",
                "Type of graph",
                choices = c("tree", "bar", "map", "3D.map"),
                selected = "tree"
              ),
              checkboxInput("bool_consol_tree",
              label = tooltip(
                    trigger = list(
                      "Apply consolidation to classes",
                      bs_icon("info-circle")
                    ),
                    "By default, k-mean consolidation is applied to classes, resulting in 
                inconsistencies between tree and clusters."
                  ),
              # "Apply consolidation to classes",
              value=TRUE),
              # helpText(HTML("By default, k-mean consolidation is applied to classes, resulting in 
                # inconsistencies between tree and clusters.")),
              checkboxInput(
                "ind_name",
                "Hide individuals name",
                value = FALSE
              ),
              conditionalPanel(
                condition = "input.type_of_plot == 'map'",
                checkboxInput(
                  "bool_draw_tree",
                  "Draw tree",
                  value = TRUE
                ),
              ),
              actionButton(
                inputId = "download_clusters",
                label = "Save plot",
                icon = icon("download"),
                class = "btn-primary",
                style = "width: 100%;"
              )
          ),
          conditionalPanel(
            condition="input.tabselected == 'parang_panel'",

              sliderInput(
                inputId = "nb_modalites_vtest",
                label = "Max. number of representatives",
                min = 1,
                max = 50,   
                value = 5,
                step = 1
              ),
              textInput("plot_title_parang", "Plot title", value = ""),
              textInput("plot_xlab_parang", "X axis title:", value = "Dimension 1"),
              textInput("plot_ylab_parang", "Y axis title", value = "Dimension 2"),
              actionButton(
                inputId = "save_cluster_v_test_post",
                label = "Save plot",
                icon = icon("download"), # FontAwesome icon before text, as in downloadButton
                class = "btn-primary", # Optional: Bootstrap color styling
                style = "width: 100%;"
              )
          ),
          conditionalPanel(
            condition="input.tabselected == 'specifs'",
              selectInput(
                inputId = "specifs_metadata_select",
                label = "Métadonnée",
                choices = metadata_name,
                selected = metadata_name[1]
              ),
              selectInput(
                inputId = "specifs_table_select",
                label = "Table de spécificités",
                choices = format_specif_choices(get_specif_candidates(metadata_name[1])),
                selected = if (length(get_specif_candidates(metadata_name[1])) > 0) get_specif_candidates(metadata_name[1])[1] else character(0)
              )
          ),

        ),
      # )
    ),
    
    # navset_pill(
    #   id = "tabselected",
        nav_panel(

          "PCA/CA",
          value = 'PCA-CA',
          # p("text"),
          conditionalPanel(
            condition = "input.analysis_method == 'PCA'",
            layout_columns(
              col_widths = c(6, 6),
              card(plotOutput("PCAplot", height = "700px")),
              card(plotOutput("PCAcircleplot", height = "700px"))
            )
          ),
          conditionalPanel(
            condition = "input.analysis_method == 'CA'",
            card(plotOutput("CAplot", height = "700px"))
          ),
        ),
        nav_panel(
          "Scree Plot",

          value = "scree",
          card(plotOutput("screePlot"))
        ),
        nav_panel(
          "Contrib. plot",
          value = 'contrib',
          card(plotOutput("contribPlot"))
        ),
        nav_panel(
          "Clustering",
          value = "clustering",
          card(
            plotOutput("clusters_plot"),

            textOutput("cluster_error_msg_hcpc"),
            card_footer("Note that, using PCA, clustering is only possible on individuals.
            One approach is to use the 'Variables by v-test' tab in the Clusters representatives panel.")
          )
        ),
        nav_panel(
          "Clusters representatives",
          value = "parang_panel",

          # card(
            # plotOutput("CA_clusters_plot"),
            # textOutput("cluster_error_msg_parang"),
            # card_footer("Depending on data size, clusters' representatives computation may take some time.")
          # )
        # ),
        # nav_panel(
          # "Data",
            # fluidRow(
              # card(
                # h4("Contingency table"),
                # column(
                  # width = 12,
                  # tags$p(
                    # style = "color: #6b7280; font-style: italic; margin-bottom: 10px;",
                    # "Éléments étudiés : Motifs"
                  # ),
                  # DTOutput("data_table")
                # ))
            # )
        # ),
        # nav_panel(
          # "Specifs",
          # value = "specifs",
          # conditionalPanel(
            # condition = "output.has_specifs_available == 'true'",
            # fluidRow(
              # card(
                # h4("Table de spécificités"),
                # column(
                  # width = 12,
                  # tags$p(
                    # style = "color: #6b7280; font-style: italic; margin-bottom: 10px;",
                    # "Éléments étudiés : Motifs"
                  # ),
                  # DTOutput("specifs_table")
                # )
              # )
            # )
          # ),
          # conditionalPanel(
            # condition = "output.has_specifs_available == 'false'",
            # card(
              # p("Aucune table de spécificités disponible pour cette analyse.")
            # )
          # )
        # ),

          # One tab per type of representative; the selected tab's value sets input$parang_paraORdist
          navset_card_tab(
            id = "parang_paraORdist",
            selected = "closest to the center (medoids)",
            nav_panel("Medoids", value = "closest to the center (medoids)",
              plotOutput("CA_clusters_plot_medoids")),
            nav_panel("Farthest from other clusters", value = "farthest from other clusters",
              plotOutput("CA_clusters_plot_dist")),
            nav_panel("Variables by v-test", value = "variable associated by v-test",
              plotOutput("CA_clusters_plot_vtest")),
            # card_footer() keeps it fixed-size; a bare tagList becomes a growing card body
            footer = card_footer(
              textOutput("cluster_error_msg_parang"),
              "Depending on data size, clusters' representatives computation may take some time."
            )
          )
        ),
        nav_panel(
          "Dataset",
            fluidRow(
              card(
                h4("Dataset"),
                column(
                  width = 12,
                  DTOutput("data_table")
                ),
              card_footer("Observations are given a rate relative to size of part (text, genre, etc.) for the PCA obs. table.")
            )
        )),

      # ),

      theme = bslib::bs_theme(),

    )




#-------------------------------
# RUN SHINY APP
#-------------------------------
args_run <- commandArgs(trailingOnly = TRUE)
host_run <- ifelse(length(args_run) >= 2, args_run[2], "127.0.0.1")
port_run <- ifelse(length(args_run) >= 3, as.integer(args_run[3]), 3838)

shiny::runApp(
  list(ui = ui, server = server),
  host = host_run,
  port = port_run,
  launch.browser = FALSE
)

