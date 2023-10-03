library(devtools)
source_url("https://raw.githubusercontent.com/M-Colley/rCode/main/r_functionality.R")

library("rstudioapi")
setwd(dirname(getActiveDocumentContext()$path))

# devtools::install_github("boxuancui/DataExplorer", ref = "develop")

library(DataExplorer)
library(data.table)

library(sjPlot)
library(sjlabelled)
library(sjmisc)

library(optimx)


# R code to grab the last directory name from a given directory path
get_last_dir_name <- function(dir_path) {
  # Split the directory path by the separator
  dir_split <- strsplit(dir_path, "/")[[1]]

  # Grab the last element from the split list, which is the last directory name
  last_dir_name <- tail(dir_split, n = 1)

  return(last_dir_name)
}





dir_paths <- c(
  "C:/Users/miuni/Desktop/SUMO-Auswertung/Ingolstadt_combined_0_2",
  "C:/Users/miuni/Desktop/SUMO-Auswertung/Monaco_0_2",
  "C:/Users/miuni/Desktop/SUMO-Auswertung/Wildau_0_2",
  "C:/Users/miuni/Desktop/SUMO-Auswertung/Ulm_0_2",
  "C:/Users/miuni/Desktop/SUMO-Auswertung/Manhattan_0_2",
  "C:/Users/miuni/Desktop/SUMO-Auswertung/Bologna_small_0_2"
)


# Loop over each directory path
for (dir_path in dir_paths) {
  # List CSV files that start with "probabilities"
  files <- list.files(
    path = dir_path,
    recursive = TRUE,
    pattern = "^probabilities.*\\.csv$",
    full.names = TRUE
  )


  # Initialize an empty data.table
  all_data <- data.table()

  # Specify the row interval
  n <- 1 # Change this to read every nth row

  # Loop through each file
  for (i in seq_along(files)) {
    file_name <- files[i]

    tryCatch(
      {
        cols_to_skip <- c("timestamp", "crossingID", "probability_estimation_method")

        # Check if the columns to skip actually exist in the file
        existing_cols <- names(fread(file_name, nrows = 0))
        cols_to_read <- setdiff(existing_cols, cols_to_skip)

        # Read every nth row
        df <- fread(file_name, select = cols_to_read)

        # Read every nth row if the data frame is not empty
        if (nrow(df) > 0) {
          df_nth_rows <- df[seq(from = n, to = nrow(df), by = n), ]
          all_data <- rbindlist(list(all_data, df_nth_rows), fill = TRUE)
        }
      },
      error = function(e) {
        message(paste("An error occurred while reading file number", i, ":", file_name))
        message("Error message:", e$message)

        # Debug: Print the column names of the problematic file
        existing_cols <- names(fread(file_name, nrows = 0))
        message("Existing columns in the file:", paste(existing_cols, collapse = ", "))
      }
    )
  }

  df_nth_rows <- NULL
  df <- NULL

  DataExplorer::create_report(all_data, output_file = paste0("report_", get_last_dir_name(dir_path = dir_path), ".html"))
}




# all_data$scenario <- as.factor(all_data$scenario)
# all_data$ehmi_density <- as.factor(all_data$ehmi_density)
# all_data$av_density <- as.factor(all_data$av_density)
# all_data$base_automated_vehicle_defiance <- as.factor(all_data$base_automated_vehicle_defiance)
# all_data$pedestrianID <- as.factor(all_data$pedestrianID)
#
# all_data$crossing_decision <- as.factor(all_data$crossing_decision)
# all_data$effective_final_crossing_probability <- as.numeric(all_data$effective_final_crossing_probability)


#
# checkAssumptionsForAnovaThreeFactors(data = all_data, y = "effective_final_crossing_probability", factor_1 = "ehmi_density", factor_2 = "av_density", factor_3 = "base_automated_vehicle_defiance")
#
#
# modelArt <- art(effective_final_crossing_probability ~ ehmi_density * av_density * base_automated_vehicle_defiance + Error(pedestrianID), data = main_df) |> anova()
# modelArt
# reportART(modelArt, dv = "effective_final_crossing_probability")
#



# modelLmer <- lmer(effective_final_crossing_probability ~ ehmi_density * av_density * base_automated_vehicle_defiance + (1|pedestrianID), data = all_data,  control = lmerControl(optimizer = "nloptwrap", calc.derivs = FALSE))
# report(modelLmer)
#
#
#
# model <- glmer(crossing_decision ~ ehmi_density * av_density * base_automated_vehicle_defiance, data = all_data, family = binomial)
# report(model)
# sjPlot::plot_model(model,
#                    title = "Effects on crossing decision during approach", sort.est = TRUE, show.values = TRUE, line.size = 0.5, dot.size = 1,
#                    vline.color = "black", value.offset = .3, show.data = TRUE,
#                    axis.labels = test) +
#   theme_bw(base_size = myfontsize - 15) + scale_y_continuous(limits = c(0.4, 2), breaks = c(.5, 1, 2)) #
