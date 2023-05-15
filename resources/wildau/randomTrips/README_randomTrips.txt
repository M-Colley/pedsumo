randomTrips

SUMO besitzt das Tool randomTrips, welches Routen innerhalb eines Netzes zufällig generiert. Aufgerufen wird das Ganze in einer batch-Datei ("randomTrips.bat").
Über den Fringe Factor, kann der Binnen- und Durchgangsverkehr gewichtet werden. Je höher die Zahl desto mehr Durchgangsverkehr wird generiert.
„P“ steht für die Period, welche angibt, wie häufig Fahrzeuge „erstellt“ werden. Je kleiner die Periode, desto mehr Fahrzeuge werden erzeugt.
Die beiden Faktoren könne so lange angepasst werden, bis das Erscheinungsbild der Simulation realistisch erscheint.

Anhand von Wildau wurden drei Methoden für randomTrips angewendet. 
Im ersten Schritt wurde die rohe Routendatei vom WebWizard ("osm.passenger.rou.xml") durchlaufen, wobei die Standardeinstellungen des Fringe Factor und der Period übernommen wurden. 
Im zweiten Schritt wurden der Fringe Factor und die Period verändert, um das gewünschte Erscheinungsbild zu erhalten (fringe factor= 7, period= 1.850).
Ein weiterer Schritt ist die Anwendung der Funktion --speed-exponent 2, wobei Kanten mit einer höheren Geschwindigkeit eine höhere Wahrscheinlichkeit erhalten, befahren zu werden.
Die Zahl hinter exponent kann beliebig gewählt werden. Die Wahrscheinlichkeit wird immer quadriert. 

Zudem ist es möglich den Fringe-Factor mit speed exponent zu kombinieren. Hierbei wird --fringe-speed-exponent aufgerufen, wobei der angebene Faktor (z.B. 2) nur auf die "fringe-Routen" angewendet wird.


Anschließend kann eine output-Datei erstellt werden, wobei die generierten Routen des Tools als Routendatei angegeben werden müssen.  
