using DataFrames, CSV, DataFramesMeta, MixedModels, Glob, CategoricalArrays, RegressionTables, FilePathsBase
using Weave, Plots, Missings, Statistics, GLM, LinearAlgebra, LaTeXStrings, TidierPlots, Images, GLM

#Pkg.add("Weave")
#scenario_name = "Ingolstadt" # for test




##### GENERAL PREPARATION ####

# Check if 'results' directory exists
if !isdir("results")
    # If it doesn't exist, create it
    mkpath("results")
end





# TODO adjust the relative paths 

# List of directory paths
dir_paths = [
    "C:/Users/miuni/Desktop/SUMO-Auswertung/Ulm_0_2",
    "C:/Users/miuni/Desktop/SUMO-Auswertung/Ingolstadt_combined_0_2",
	"C:/Users/miuni/Desktop/SUMO-Auswertung/Wildau_0_2",
	"C:/Users/miuni/Desktop/SUMO-Auswertung/Bologna_small_0_2",
	"C:/Users/miuni/Desktop/SUMO-Auswertung/Monaco_0_2",
	"C:/Users/miuni/Desktop/SUMO-Auswertung/Manhattan_0_2"
]



# Loop over each directory path
for dir_path in dir_paths

	# Initialize an empty DataFrame
	all_data = DataFrame()


	# Directory path for test
	#dir_path = "C:/Users/miuni/Desktop/SUMO-Auswertung/Ingolstadt_combined_0_2"

	scenario_name = basename(dir_path)

	#######################
	#### GATHER DATA ######
	#######################

	function list_csv_files_recursive(dir_path::String)
		result = String[]
		for entry in readdir(dir_path, join=true)
			if isdir(entry)
				result = vcat(result, list_csv_files_recursive(entry))
			elseif startswith(basename(entry), "probabilities") && endswith(entry, ".csv")
				push!(result, entry)
			end
		end
		return result
	end

	files = list_csv_files_recursive(dir_path)
	#println(files)

	# Loop through each file
	for file_name in files
		try
			df = DataFrame(CSV.File(file_name))
			if nrow(df) > 0
				all_data = vcat(all_data, df)
			end
		catch e
			println("An error occurred while reading file: $file_name")
			println("Error message: ", e)

			try
				existing_cols = names(DataFrame(CSV.File(file_name; limit=0)))
				println("Existing columns in the file: ", join(existing_cols, ", "))
			catch inner_e
				println("Could not retrieve column names. Error: ", inner_e)
			end
		end
	end


	#df = nothing
	#print(all_data)

	#######################
	#### PREPARE DATA #####
	#######################

	#all_data = dropmissing(all_data)

	all_data.scenario = categorical(all_data.scenario)
	all_data.ehmi_density = round.(all_data.ehmi_density, digits=2)
	all_data.av_density = round.(all_data.av_density, digits=2)
	all_data.base_automated_vehicle_defiance = round.(all_data.base_automated_vehicle_defiance, digits=2)

	all_data.ehmi_density = categorical(all_data.ehmi_density)
	all_data.av_density = categorical(all_data.av_density)
	all_data.base_automated_vehicle_defiance = categorical(all_data.base_automated_vehicle_defiance)
	all_data.pedestrianID = categorical(all_data.pedestrianID)
	all_data.dangerous_situation = categorical(all_data.dangerous_situation)


	all_data.crossing_decision = categorical(all_data.crossing_decision)
	all_data.effective_final_crossing_probability = float.(all_data.effective_final_crossing_probability)



	###############################
	#### EVALUATE CUSTOM DATA #####
	###############################



	##########
	# dangerous_situation
	##########
	model_dangerous_situation = fit!(LinearMixedModel(@formula(dangerous_situation ~ ehmi_density * av_density * base_automated_vehicle_defiance + (1|pedestrianID)), all_data))
	model_dangerous_situation
	regtable(model_dangerous_situation; renderSettings = htmlOutput("results/" * scenario_name * "_dangerous_situation_model.html"))
	regtable(model_dangerous_situation; renderSettings = latexOutput("results/" * scenario_name * "_dangerous_situation_model.tex"))


	##########
	# effective_final_crossing_probability with interaction effects
	##########

	model = fit!(LinearMixedModel(@formula(effective_final_crossing_probability ~ ehmi_density * av_density * base_automated_vehicle_defiance + (1|pedestrianID)), all_data))
	model

	regtable(model; renderSettings = latexOutput("results/" * scenario_name * "_effective_final_crossing_probability_model.tex"))
	regtable(model; renderSettings = htmlOutput("results/" * scenario_name * "_effective_final_crossing_probability_model.html"))


	# Extracting relevant data from the model
	fixed_effects_summary = coef(model)  # Fixed effects coefficients
	random_effects_summary = ranef(model) # Random effects
	residuals_data = residuals(model)  # Residuals
	predicted_data = predict(model)  # Predicted values
	observed_data = all_data.effective_final_crossing_probability  # Observed values

	# Creating subplots
	p1 = scatter(observed_data, predicted_data, title="Predicted vs Observed", xlabel="Observed", ylabel="Predicted", legend=false, alpha=0.15)
	p2 = scatter(residuals_data, title="Residual Plot", xlabel="Observation", ylabel="Residual", legend=false, alpha=0.15)

	# Combining subplots into a single plot
	plot(p1, p2, layout=(1, 2), legend=false)
	savefig("results/" * scenario_name * "_probability_crossing_combined.png")



	plot(all_data.av_density, predict(model), color = :green, linewidth = 3, title = "Predicted values for Final Crossing Probability", ylabel = "Final Crossing Prob. Predicted", xlabel = "AV density", legend = false)
	savefig("results/" * scenario_name * "_probability_crossing_av_density.png")

	plot(all_data.ehmi_density, predict(model), color = :green, linewidth = 3, title = "Predicted values for Final Crossing Probability", ylabel = "Final Crossing Prob. Predicted", xlabel = "eHMI density", legend = false)
	savefig("results/" * scenario_name * "_probaility_crossing_ehmi_density.png")


	####################################
	#### TESTING GGPLOT EQUIVALENT #####
	####################################

	# does not work
	#all_data.av_density = float.(all_data.av_density)
	# Convert to float array
	# Convert CategoricalValue to Float64
	#all_data.av_density = Float64[get(all_data.av_density[i]) for i in 1:length(all_data.av_density)]

	# p= @ggplot(all_data, aes(x = av_density, y = effective_final_crossing_probability, color = ehmi_density)) + 
	#     @geom_point() + 
	#     @geom_smooth(method = "lm") +
	#     @labs(x = "AV density", y = "Prediction") +
	#     theme_minimal()

	# savefig(p, "results/" * scenario_name * "_test_ggplot.png")



	###########################################
	#### GENERATE HEATMAP OF INTERACTIONS #####
	###########################################

	# Define a custom color gradient in shades of purple
	purple_gradient = cgrad([:red, :purple])	

	# ATTENTION: HERE, the y-values are swapped!
	#histogram2d(all_data[:, :pedestrian_location_x], all_data[:, :pedestrian_location_y], bins=(1000,1000), color=purple_gradient, opacity=0.5, xlabel="X", ylabel="Y", title="2D Histogram")
	#savefig("heatmap_Ingolstadt_1.png")














	####################################
	#### EVALUATE SUMO STATS ###########
	####################################

	# Initialize an empty DataFrame
	stats_all_data = DataFrame()

	function list_stats_csv_files_recursive(dir_path::String)
		result = String[]
		for entry in readdir(dir_path, join=true)
			if isdir(entry)
				result = vcat(result, list_stats_csv_files_recursive(entry))
			elseif startswith(basename(entry), "stats") && endswith(entry, ".csv")
				push!(result, entry)
			end
		end
		return result
	end

	stats_files = list_stats_csv_files_recursive(dir_path)
	#println(files)

	####### Merge stats file with the independent variables


	# Loop through each file
	for file_name in stats_files
		try
			#print(file_name)
			df = DataFrame(CSV.File(file_name))
			
			# Get the directory of the stats file
			stats_dir = dirname(file_name)
			
			# Find the corresponding probabilities file
			prob_file = first(list_csv_files_recursive(stats_dir))
			
			# Read the scenario from the probabilities file
			prob_df = DataFrame(CSV.File(prob_file, limit=1))  # Read only the first row to get the scenario
			scenario = prob_df.scenario[1]
			ehmi_density = prob_df.ehmi_density[1]
			av_density = prob_df.av_density[1]
			base_automated_vehicle_defiance = prob_df.base_automated_vehicle_defiance[1]
					
			# Add the scenario to the stats DataFrame
			df.scenario = fill(scenario, nrow(df))
			df.ehmi_density = fill(ehmi_density, nrow(df))
			df.av_density = fill(av_density, nrow(df))
			df.base_automated_vehicle_defiance = fill(base_automated_vehicle_defiance, nrow(df))
			
			if nrow(df) > 0
				stats_all_data = vcat(stats_all_data, df)
			end
		catch e
			# Error handling code (unchanged)
		end
	end




	#######################
	#### PREPARE DATA #####
	#######################

	#stats_all_data = dropmissing(stats_all_data)
	#print(stats_all_data)


	stats_all_data.scenario = categorical(stats_all_data.scenario)

	stats_all_data.ehmi_density = round.(stats_all_data.ehmi_density, digits=2)
	stats_all_data.av_density = round.(stats_all_data.av_density, digits=2)
	stats_all_data.base_automated_vehicle_defiance = round.(stats_all_data.base_automated_vehicle_defiance, digits=2)

	stats_all_data.ehmi_density = categorical(stats_all_data.ehmi_density)
	stats_all_data.av_density = categorical(stats_all_data.av_density)
	stats_all_data.base_automated_vehicle_defiance = categorical(stats_all_data.base_automated_vehicle_defiance)

	stats_all_data.pedestrianStatistics_duration = float.(stats_all_data.pedestrianStatistics_duration)
	stats_all_data.pedestrianStatistics_routeLength = float.(stats_all_data.pedestrianStatistics_routeLength)
	stats_all_data.vehicleTripStatistics_totalTravelTime = float.(stats_all_data.vehicleTripStatistics_totalTravelTime)
	stats_all_data.vehicleTripStatistics_speed = float.(stats_all_data.vehicleTripStatistics_speed)
	stats_all_data.vehicleTripStatistics_duration = float.(stats_all_data.vehicleTripStatistics_duration)
	stats_all_data.safety_collisions = float.(stats_all_data.safety_collisions)



	##############
	# safety_collisions with interaction effects
	##############



	#model_collisions = fit(LinearModel, @formula(safety_collisions ~ ehmi_density * av_density * base_automated_vehicle_defiance), stats_all_data)
	# TODO some error occurs here
	#model_collisions = lm(@formula(safety_collisions ~ ehmi_density * av_density * base_automated_vehicle_defiance), stats_all_data)
	#model_collisions
	#print(StatsModels.TableRegressionModel{LinearModel{GLM.LmResp{Vector{Float64}}, GLM.DensePredChol{Float64, LinearAlgebra.CholeskyPivoted{Float64, Matrix{Float64}}}}, Matrix{Float64}})

	#regtable(model_collisions; renderSettings = htmlOutput("results/" * scenario_name * "_persons_collisions.html"))
	#regtable(model_collisions; renderSettings = latexOutput("results/" * scenario_name * "_persons_collisions.tex"))

	#fitted_model_collisions = predict(model_collisions)

	# Create the plot
	#plot(fitted_model_collisions, seriestype=:scatter, xlabel="Fitted Values", ylabel="Residuals")
	#savefig("results/" * scenario_name * "_general_model_collisions.png")



	##############
	# safety_collisions ~ av_density
	##############

	model_collisions_av_density = lm(@formula(safety_collisions ~ av_density), stats_all_data)
	model_collisions_av_density
	print(StatsModels.TableRegressionModel{LinearModel{GLM.LmResp{Vector{Float64}}, GLM.DensePredChol{Float64, LinearAlgebra.CholeskyPivoted{Float64, Matrix{Float64}}}}, Matrix{Float64}})


	fitted_model_collisions_av_density = predict(model_collisions_av_density)

	# Create the plot
	plot(fitted_model_collisions_av_density, seriestype=:scatter, xlabel="Fitted Values", ylabel="Residuals")
	savefig("results/" * scenario_name * "_collisions_av_density_unwanted.png")

	p = plot(stats_all_data.av_density, stats_all_data.safety_collisions, seriestype=:scatter, smooth= :true, xlabel="AV density", ylabel="Collisions")
	annotate!(
	  3,
	  0.5,
	  latexstring(
		"y = $(round(coef(model_collisions_av_density)[2], digits = 2))x + $(round(coef(model_collisions_av_density)[1], digits = 2))"
	  )
	)

	annotate!(
	  3,
	  0.4,
	  latexstring("r^2 = $(round(r2(model_collisions_av_density), digits = 2))")
	)


	savefig("results/" * scenario_name * "_collisions_av_density.png")



	regtable(model_collisions_av_density; renderSettings = htmlOutput("results/" * scenario_name * "_model_collisions_av_density.html"))
	regtable(model_collisions_av_density; renderSettings = latexOutput("results/" * scenario_name * "_model_collisions_av_density.tex"))


	##############
	# safety_collisions ~ ehmi_density
	##############

	model_collisions_ehmi_density = lm(@formula(safety_collisions ~ ehmi_density), stats_all_data)
	model_collisions_ehmi_density
	#print(StatsModels.TableRegressionModel{LinearModel{GLM.LmResp{Vector{Float64}}, GLM.DensePredChol{Float64, LinearAlgebra.CholeskyPivoted{Float64, Matrix{Float64}}}}, Matrix{Float64}})


	regtable(model_collisions_ehmi_density; renderSettings = htmlOutput("results/" * scenario_name * "_model_collisions_ehmi_density.html"))
	regtable(model_collisions_ehmi_density; renderSettings = latexOutput("results/" * scenario_name * "_model_collisions_ehmi_density.tex"))


	##############
	# safety_collisions ~ base_automated_vehicle_defiance
	##############


	model_collisions_base_automated_vehicle_defiance = lm(@formula(safety_collisions ~ base_automated_vehicle_defiance), stats_all_data)
	model_collisions_base_automated_vehicle_defiance
	#print(StatsModels.TableRegressionModel{LinearModel{GLM.LmResp{Vector{Float64}}, GLM.DensePredChol{Float64, LinearAlgebra.CholeskyPivoted{Float64, Matrix{Float64}}}}, Matrix{Float64}})


	regtable(model_collisions_base_automated_vehicle_defiance; renderSettings = htmlOutput("results/" * scenario_name * "_model_collisions_base_automated_vehicle_defiance.html"))
	regtable(model_collisions_base_automated_vehicle_defiance; renderSettings = latexOutput("results/" * scenario_name * "_model_collisions_base_automated_vehicle_defiance.tex"))












	##############
	# vehicleTripStatistics_duration with interaction effects
	##############

	#model_duration = fit(LinearModel, @formula(vehicleTripStatistics_duration ~ ehmi_density * av_density * base_automated_vehicle_defiance), stats_all_data)
	#model_duration
	#print(StatsModels.TableRegressionModel{LinearModel{GLM.LmResp{Vector{Float64}}, GLM.DensePredChol{Float64, LinearAlgebra.CholeskyPivoted{Float64, Matrix{Float64}}}}, Matrix{Float64}})


	#regtable(model_duration; renderSettings = htmlOutput("results/" * scenario_name * "_persons_duration.html"))
	#regtable(model_duration; renderSettings = latexOutput("results/" * scenario_name * "_persons_duration.tex"))


	##############
	# vehicleTripStatistics_duration ~ av_density
	##############

	model_duration_av_density = lm(@formula(vehicleTripStatistics_duration ~ av_density), stats_all_data)
	model_duration_av_density
	print(StatsModels.TableRegressionModel{LinearModel{GLM.LmResp{Vector{Float64}}, GLM.DensePredChol{Float64, LinearAlgebra.CholeskyPivoted{Float64, Matrix{Float64}}}}, Matrix{Float64}})


	#fitted_model_duration_av_density = predict(model_duration_av_density)

	# Create the plot
	# plot(fitted_model_duration_av_density, seriestype=:scatter, xlabel="Fitted Values", ylabel="Residuals")
	# savefig("results/" * scenario_name * "_duration_av_density.png")

	#scatter(df.x, df.y, smooth = :true, label = "data")
	p = plot(stats_all_data.av_density, stats_all_data.vehicleTripStatistics_duration, seriestype=:scatter, smooth= :true, xlabel="AV density", ylabel="Duration")
	annotate!(
	  4,
	  593,
	  latexstring(
		"y = $(round(coef(model_duration_av_density)[2], digits = 2))x + $(round(coef(model_duration_av_density)[1], digits = 2))"
	  )
	)

	annotate!(
	  4,
	  592.75,
	  latexstring("r^2 = $(round(r2(model_duration_av_density), digits = 2))")
	)

	savefig("results/" * scenario_name * "_duration_av_density.png")



	regtable(model_duration_av_density; renderSettings = htmlOutput("results/" * scenario_name * "_model_duration_av_density.html"))
	regtable(model_duration_av_density; renderSettings = latexOutput("results/" * scenario_name * "_model_duration_av_density.tex"))






	##############
	# vehicleTripStatistics_duration ~ ehmi_density
	##############



	model_duration_ehmi_density = lm(@formula(vehicleTripStatistics_duration ~ ehmi_density), stats_all_data)
	model_duration_ehmi_density
	print(StatsModels.TableRegressionModel{LinearModel{GLM.LmResp{Vector{Float64}}, GLM.DensePredChol{Float64, LinearAlgebra.CholeskyPivoted{Float64, Matrix{Float64}}}}, Matrix{Float64}})


	regtable(model_duration_ehmi_density; renderSettings = htmlOutput("results/" * scenario_name * "_model_duration_ehmi_density.html"))


	##############
	# vehicleTripStatistics_duration ~ base_automated_vehicle_defiance
	##############

	model_duration_base_automated_vehicle_defiance = lm(@formula(vehicleTripStatistics_duration ~ base_automated_vehicle_defiance), stats_all_data)
	model_duration_base_automated_vehicle_defiance
	#print(StatsModels.TableRegressionModel{LinearModel{GLM.LmResp{Vector{Float64}}, GLM.DensePredChol{Float64, LinearAlgebra.CholeskyPivoted{Float64, Matrix{Float64}}}}, Matrix{Float64}})


	regtable(model_duration_base_automated_vehicle_defiance; renderSettings = htmlOutput("results/" * scenario_name * "_model_duration_base_automated_vehicle_defiance.html"))
	regtable(model_duration_base_automated_vehicle_defiance; renderSettings = latexOutput("results/" * scenario_name * "_model_duration_base_automated_vehicle_defiance.tex"))

end