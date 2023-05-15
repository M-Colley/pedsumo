This tutorial shows how routes within a network can be generated using counting data. Different tools can be used for route definition or can also be created by hand.
The entire procedure is explained using the example of the city of Wildau (Germany, Brandenburg).
The results were created within a project of the bachelor's degree course in traffic systems technology at the Technical University of Wildau.

Introduction:
The network ("Netzmodell2.xml") and the flow file ("flows_SUMOV2.2.rou.xml") are the basis for the individual tools. In most batch files includes the network file.
The current version of the flow file is based on the manually defined routes for vehicles using the main road network. The number of vehicles results from the counting data about 18 positions.
With the help of the presented tools, an overview should be given of how routes can be automatically generated and evaluated by SUMO using the counting data.


Importtant: 
In order to be able to execute the batch files, the network file must be specified correctly. In this case it is referred to in the batch files with ../ in front of the network file.
Alternatively, the network file must be available in every subfolder.
Every folde includes an cofiguration-file, which presentet the results of every tool. 

Evaluation: 
It is interesting to see whether SUMO  was able to convert the counting data at the counting points. To compare the input with the output an output file can be created.
To do this, an additional file must first be written (see additional.add.xml), which is then written to a batch file (see output_configuration.bat).
At first the batch file must be executed and then should be a configuration file "saved". This must now be played in order to receive the output file, which was named in the additional file.
Now the edge IDs of the counting positions can be searched for and compared in the file.
To make the work easier, the output configuration files are already in each folder, which means that a separate batch file no longer has to be written.
Only the files (network, routes and additional) must / can be adapted.


An Excel table, which compares the counting data and the output data, can be used as an evaluation option or comparability. Now, for example, the square deviation of the individual data can be calculated.
And finally the RMS can be formed. The number makes it clear which tool / variant receives the lowest value.
The attached Python script can be used as an alternative to the manual calculation of the RMS in Excel. Only the second xml-file has to be transferred.