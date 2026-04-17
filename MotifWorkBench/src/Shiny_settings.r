library(shiny)
library(bslib)
library(httr)
library(commonmark)
library(shinyFiles)

ui <- page_navbar( 
  nav_panel("Basic",
    navset_card_underline(
      nav_panel(
        title="Basics",
        h4("NLP"),
        fluidRow(
          column(4,
            textInput(
            inputId = "stanza_lang",
            label = "Stanza code for language:",
            value = "fr"
            ),
            checkboxInput("stanza_use_GPU",
              "Use GPU",
              value=FALSE
            ),
          ),
          column(8,
            helpText(HTML('Tagging is performed through Stanza. You can change
            language using the lcode listed on their
            <a href="https://stanfordnlp.github.io/stanza/performance.html" target="_blank">Performance</a> page.<br/>
            Tagging large corpora with Stanza can be slow. You can chose to pre-tag
            your texts and then place them into MWB <i>Textes_tagged_stanza</i>
            directory; MWB will by-pass tagging if texts are already tagged.'))
          ),
        ),
        h4("Textometry interface"),
        fluidRow(
          column(4,
            checkboxGroupInput(
              inputId = "type_of_CA",
              label = "Perform CA",
              choices = c("Through Graphic User Interface",
                          "Without Graphic User Interface"),
              selected = "Through Graphic User Interface",
            ),
          ),
          column(8,
            helpText(HTML("Correspondance Analysis (french: <i>Analyse Factorielle de Correspondance</i>)
              can be performed with a Graphic User Interface (GUI), automatically
              (without GUI: a set a plots is saved to the computer with no customization)
              or can be by-passed (leave both checkboxes unchecked)."))
          )
        ),
        h4("Data"),
          fluidRow(
            column(4,
              fileInput("files", "Load/change corpus", multiple = TRUE, accept = ".txt"),
              actionButton("process", "Replace current corpus by the selected files", width = 300),
              verbatimTextOutput("status")
            ),
            column(8,
              helpText(HTML("MWB corpus is loaded in <code>Data/Textes_raw/</code>. You can run MWB on the
              current <code>Data/Textes_raw/</code> corpus or use <code>Load/change corpus</code> to replace
              the corpus by a new one.")),
              div(style = "height: 10px;"),
              helpText(HTML("<span style='font-weight:bold;'>⚠ Changing the corpus will overwrite every files
              (tagged files, processed for extraction files, motifs, etc.) ⚠</span>")),
              div(style = "height: 10px;"),
              helpText(textOutput("n_texts"))
            )
          ),
        fluidRow(
          column(4,
            fileInput("select_metadata", "Load/change metadata.tsv", multiple = TRUE, accept = ".tsv")
          ),
          column(8,
            helpText(HTML("Defaut MWB metadata file is <code>Data/metadata.tsv</code>; you can select another
            metadata file. The metadata file should be a <code>.tsv</code>. Update the subcorpora splitting
            settings according to this file.")),
            div(style = "height: 10px;"),
            helpText(htmlOutput("metadata_path"))
          )
        ),
        fluidRow(
          column(4, 
            checkboxInput("clean_previous_run",
                "Clean previous run (delete all results in MWB directories)",
                value=FALSE
            )
          ),
          column(8, 
            helpText(HTML("To run CWB on a new corpus or with different motifs setttings,
            purge motifs mined by previous runs of MWB. Use with caution!"))
          )
        ),
      ),
      nav_panel(
        title="Pattern mining",
        h4("Motifs representation"),
          checkboxGroupInput(
            inputId = "show_items",
            label = "Items for pattern mining:",
            choices = c("Form",
                        "Lemma",
                        "POS",
                        "Dep",
                        "Feats",
                        "Wordpieces"),
            selected = c("Lemma",
                        "POS",
                        "Dep"),
          ),
        h4("Pattern mining settings"),
          textInput(
            inputId = "list_itemset_min",
            label = "Minimal size(s) of motifs (itemset_min):",
            value = 3
          ),
          textInput(
            inputId = "list_itemset_min",
            label = "Minimal frequency/ies for a pattern to be a recurrent motif (min_percent):",
            value = "25, 10, 5"
          ),
          textInput(
            inputId = "gap_max",
            label = "Gap tolerance(s) (gap_max):",
            value = 0
          ),
          textInput(
            inputId = "gap_min",
            label = "Gap requirement(s) (gap_min):",
            value = 0
          ),
          helpText(HTML("Lexicon:
                        <ul>
                            <li>Item: a property of a linguistic unit (e.g., its
                              lemma)</li>
                            <li>Itemset: a linguistic unit (e.g., a word)</li>
                              <ul>
                                <li>Motifs (patterns) are sets of itemsets defined by
                                  one or several items</li>
                              </ul>
                            <li>(Max/min) gap: tolerance/requirement of a number of
                              exogeneous itemsets in motifs</li>
                          </ul>
                        You can pass multiple, comma-separated values to
                              fields, in which case pattern mining is performed for
                              every combinaison of this values. Beware of
                              computation time!")),
        h4("Clustering of patterns"),
          checkboxGroupInput(
            inputId = "type_of_clustering",
            label = "Type(s) of clustering",
            choices = c("Perform clustering before CA (makes CA faster)"),
            selected = "Perform clustering before CA (makes CA faster)",
          ),
      ),
      nav_panel(
        title="Browse metadata",
        card(
          card_header("Metadata table"),
          dataTableOutput(outputId = "metadata_table"),
        ),
        card(
          card_header("Distribution of metadata"),
          fluidRow(
            column(6,
              selectInput(
                "plot_mode",
                "What to display?",
                choices = c(
                  "Unique values per column" = "unique_cols",
                  "Levels of selected column" = "levels_col"
                )
              ),
            ),
            column(6,
              uiOutput("col_selector")
            )
          ),
          plotOutput("metadata_plot")
        )
      ),
    )
  ),
    # card(
    #   card_header("NLP"),
    #   fluidRow(
    #     column(6,
    #       textInput(
    #       inputId = "stanza_lang",
    #       label = "Stanza code for language:",
    #       value = "fr"
    #       ),
    #       checkboxInput("stanza_use_GPU",
    #         "Use GPU",
    #         value=FALSE
    #       ),
    #     ),
    #     column(6,
    #       helpText(HTML('Tagging is performed through Stanza. You can change
    #       language using the lcode listed on their
    #       <a href="https://stanfordnlp.github.io/stanza/performance.html" target="_blank">Performance</a> page.<br/>
    #       Tagging large corpora with Stanza can be slow. You can chose to pre-tag
    #       your texts and then place them into MWB <i>Textes_tagged_stanza</i>
    #       directory; MWB will by-pass tagging if texts are already tagged.'))
    #     ),
    #   ),
    # # ),
    # card(
    #   card_header("Correspondance Analysis"),
    #   fluidRow(
    #     column(6,
    #       checkboxGroupInput(
    #         inputId = "type_of_CA",
    #         label = "Perform CA",
    #         choices = c("Through Graphic User Interface",
    #                     "Without Graphic User Interface"),
    #         selected = "Through Graphic User Interface",
    #       ),
    #     ),
    #     column(6,
    #       helpText(HTML("Correspondance Analysis (french: <i>Analyse Factorielle de Correspondance</i>)
    #     can be performed with a Graphic User Interface (GUI), automatically
    #     (without GUI: a set a plots is saved to the computer with no customisation)
    #     or can be by-passed (leave both checkboxes unchecked)."))
    #     )
    #   )
    # ),
    # card(
    #   card_header("Clean previous run"),
    #   fluidRow(
    #     column(6, 
    #       checkboxInput("clean_previous_run",
    #           "Clean previous run (delete all results in MWB directories)",
    #           value=FALSE
    #       )
    #     ),
    #     column(6, 
    #       helpText(HTML("To run CWB on a new corpus or with different motifs setttings,
    #       purge motifs mined by previous runs of MWB. Use with caution!"))
    #     )
    #   ),
    # ),



    # h4("Clustering"),
    #   checkboxGroupInput(
    #     inputId = "type_of_clustering",
    #     label = "Type(s) of clustering",
    #     choices = c("Perform clustering before CA (makes CA faster)",
    #                 "Perform clustering of patterns"),
    #     selected = "Perform clustering before CA (makes CA faster)",
    #   ),
    #   helpText(HTML("Two different types of clustering is available. Clustering
    #                 before CA is meant to alleviate computation for performing
    #                 CA. Clustering of patterns is a different set of clustering
    #                 methods, independant from CA.<br/>
    #                 Note that CA computation also performs its own clustering.<br/>
    #                 Note that performing CA on large data-set without preprocessing
    #                 clusterings can make CA comptation very slow.")),
      # checkboxGroupInput(
      #   inputId = "show_items",
      #   label = "Items for pattern mining:",
      #   choices = c("Form",
      #               "Lemma",
      #               "POS",
      #               "Dep",
      #               "Feats",
      #               "Wordpieces"),
      #   selected = c("Lemma",
      #                "POS",
      #                "Dep"),
      # ),
    #   textInput(
    #     inputId = "list_itemset_min",
    #     label = "Minimal size(s) of motifs (itemset_min):",
    #     value = 3
    #   ),
    #   textInput(
    #     inputId = "list_itemset_min",
    #     label = "Minimal frequency/ies for a pattern to be a recurrent motif (min_percent):",
    #     value = "25, 10, 5"
    #   ),
    #   textInput(
    #     inputId = "gap_max",
    #     label = "Gap tolerance(s) (gap_max):",
    #     value = 0
    #   ),
    #   textInput(
    #     inputId = "gap_min",
    #     label = "Gap requirement(s) (gap_min):",
    #     value = 0
    #   ),
    #   helpText(HTML("Lexicon:
    #                 <ul>
    #                     <li>Item: a property of a linguistic unit (e.g., its
    #                       lemma)</li>
    #                     <li>Itemset: a linguistic unit (e.g., a word)</li>
    #                       <ul>
    #                         <li>Motifs (patterns) are sets of itemsets defined by
    #                           one or several items</li>
    #                       </ul>
    #                     <li>(Max/min) gap: tolerance/requirement of a number of
    #                       exogeneous itemsets in motifs</li>
    #                   </ul>
    #                 You can pass multiple, comma-separated values to
    #                       fields, in which case pattern mining is performed for
    #                       every combinaison of this values. Beware of
    #                       computation time!"))
    # ),
    nav_panel("References",
      uiOutput("readme")
    ),
    
  title = "MWB: Motif Work Bench settings", 
  id = "page", 
) 

server <- function(input, output) {
  output$readme <- renderUI({
    url <- "https://raw.githubusercontent.com/HugoDumoulin0/MotifWorkBench/blob/main/README.md"
    
    res <- GET(url)
    stop_for_status(res)
    
    md <- content(res, as = "text", encoding = "UTF-8")
    
    HTML(markdown_html(md))
  })

  # Count files in data
  rv <- reactiveValues(refresh = 0)
    observeEvent(input$process, {
      rv$refresh <- rv$refresh + 1
    })
    corpus_n <- reactive({
      rv$refresh
      target_dir <- normalizePath("../Data/Textes_raw", mustWork = FALSE)
      if (!dir.exists(target_dir)) return(0)
      length(list.files(target_dir))
    })
  output$n_texts <- renderText({
    paste("Number of files in the corpus:", corpus_n())
  })

  #Change corpus
  target_dir <- normalizePath("../Data/Textes_raw", mustWork = FALSE)
    observeEvent(input$process, {
      req(input$files)
      # 1. Create directory if it doesn't exist
      if (!dir.exists(target_dir)) {
        dir.create(target_dir, recursive = TRUE)
      }
      # 2. Empty directories
      dirs_to_clean <- c(
        "../Data/Textes_raw",
        "../Data/cwb-corpus",
        "../Data/DMT4_files",
        "../Data/Lexiques",
        "../Data/Textes_tagged_stanza",
        "../Data/Textes_tagged_stanza_for_dmt4",
        "../Data/textesVRT",
        "../Data/underscore_fix",
        "../Clustering_results",
        "../Patterns_results"
      )
      for (dir in dirs_to_clean) {
        dir_path <- normalizePath(dir, mustWork = FALSE)
        if (dir.exists(dir_path)) {
          files <- list.files(dir_path, full.names = TRUE, recursive = FALSE)
          if (dir.exists(dir_path)) {
            unlink(list.files(dir_path, full.names = TRUE), recursive = TRUE)
          }
        }
      }
      # 3. Copy uploaded files
      file.copy(
        from = input$files$datapath,
        to = file.path(target_dir, input$files$name),
        overwrite = TRUE
      )
      output$status <- renderText({
        paste("Copied", nrow(input$files), "files to:", target_dir)
      })
    })

    #Select metadata
    output$metadata_path <- renderText({
      input$select_metadata  # <-- forces reactivity
      path <- "../Data/metadata.tsv"
      if (!file.exists(metadata_path())) {
        return("No metadata file. Needed to run MWB!")
      }
      paste0("metadata file is: <code>", metadata_path(), "</code>")
    })

    #Display metadata
    metadata_path <- reactive({
      # 1. If user uploaded a file
      if (!is.null(input$select_metadata)) {
        return(normalizePath(input$select_metadata$datapath, mustWork = FALSE))
      }
      # 2. Default file
      default_path <- "../Data/metadata.tsv"
      normalizePath(default_path, mustWork = FALSE)
    })
    metadata_df <- reactive({
      req(file.exists(metadata_path()))
      read.delim(
        metadata_path(),
        sep = "\t",
        stringsAsFactors = FALSE
      )
    })
    output$metadata_table <- DT::renderDT({metadata_df()})
    output$col_selector <- renderUI({
      selectInput(
        "selected_col",
        "Select column",
        choices = names(metadata_df())
      )
    })
    output$metadata_plot <- renderPlot({
      mode <- input$plot_mode
      if (mode == "unique_cols") {
        counts <- sapply(metadata_df(), function(x) length(unique(x)))
        barplot(
          sort(counts, decreasing = TRUE),
          las = 2,
          col = "steelblue",
          main = "Columns of metadata",
          ylab = "Unique values"
        )
      } else if (mode == "levels_col") {
        req(input$selected_col)
        col <- metadata_df()[[input$selected_col]]
        counts <- sort(table(col), decreasing = TRUE)
        barplot(
          counts,
          las = 2,
          col = "darkorange",
          main = paste("Levels of", input$selected_col),
          ylab = "Nb of texts"
        )
      }
    })
}

shiny::runApp(list(ui = ui, server = server),
              launch.browser = TRUE)
