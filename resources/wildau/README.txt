Dieses Tutorial zeigt, wie mithilfe von Zähldaten Routen innerhalb eines Netzes generiert werden können. Hierbei können verschiedene Tools für die Routendefinition verwendet werden oder aber auch per Hand angelegt werden.
Erklärt wird das gesamte Verfahren am Bespiel der Stadt Wildau (Deutschland, Brandenburg).
Die Ergebnisse entstanden innerhalb eines Projektes des Bachelorstudienganges Verkehrssystemtechnik der Technischen Hochschule Wildau. 

Nützliche Links zum Umsetzen der einzelnen Tools: 
•	SUMO Benutzerdokumentation -> grundlegende Verwendungen 
•	Tutorials
•	Documentation 
o	Netedit
o	Simulation
o	Werkzeuge 
	Detektor -> flowrouter
	Trip -> randomTrips
	Turns -> routeSampler
o	Definition of vehicles, vehicle types and routes 
o	Importing networks with netconvert


Einstieg: 
Als Basis für die einzelnen Tools dient das Netz ("Netzmodell2.xml") und die Flow-Datei ("flows_SUMOV2.2.rou.xml"). In den meisten batch-Dateien wird insbesondere der Netz-File benötigt. 
Die Flow-Datei basiert in der jetzigen Fassung auf händisch definierten Routen der Fahrzeuge, welche das Hauptstraßennetz befahren. Die Anzahl der Fahrzeuge ergibt sich aus Zähldaten, welche von 18 Positionen vorlagen. 
Mithilfe der vorgstellten Tools soll eine Übersicht gegeben werden, wie Routen von SUMO automatisch generiert und ausgewertet können mithilfe der Zähldaten. 

Wichtig: 
Um die batch-Dateien ausführen zu können muss der Netz-File korrekt angegeben werden. In diesem Fall wird in den batch-Dateien mit ../ vor dem Netz-File darauf verwiesen. 
Alternativ muss der Netz-File in jedem Unterordner vorhanden sein. 
In jedem Ordner ist zudem eine Konfiguariontsdatei vorgesehen, welche die Ergebnisse der Tools "grafisch" darstellt. 

Auswertung: 
Interessant ist es zu sehen, ob SUMO die Zähldaten an den Zählstellen auch "wirklich" umsetzten kann/konnte. Um den Input mit dem Ouput vergleichen zu können, kann eine output-Datei erstellt werden. 
Hierzu muss zunächst ein additional-File geschrieben werden (siehe additional.add.xml), welcher dann in eine batch-Datei (siehe output_configuration.bat) geschrieben wird. 
Zunächst wird dann die batch-Datei ausgeführt, wobei eine Konfigurationsdatei "gespeichert" wird. Diese muss nun abgespielt werden, um die output-Datei, welche im additional-File benannt wurde, zu erhalten. 
Nun können in der Datei die Edge-ID´s der Zählpositionen gesucht und verglichen werden.
Um die Arbeit zu erleichtern, befinden sich in jedem Ordner bereits die output-Konfigurationsdateien, wodurch keine separate batch-Datei mehr geschrieben werden muss.
Lediglich die Files (Netz, Routen und Additional) müssen/können angepasst werden.  

Als Auswertmöglichkeit bzw. Vergleichbarkeit bietet sich hier eine Excel-Tabelle an, welche die Zähldaten und die output-Daten gegenüberstellt. Nun kann z.B. die quadratische Abweichung der einzelnen Daten berechnet werden. 
Und abschließend kann der RMS gebildet werden. Anhand der Zahl wird deutlich, welches Tool/Variante den kleinsten Wert erhält.
Als Alternative zur händischen Berechnung des RMS in Excel kann das beigefügte Python-Skript verwendet werden. Hierbei muss lediglich die zweite übergebene XML-Datei beliebig angepasst werden.  

Als Inspiration befindet sich in diesen Ordner eine Excel-Tabelle mit den Ergebnissen des Porjektes, dargestellt in Diagrammen. Zum einen der RMS der einzelnen Tools, zum anderen die Zählwerte an drei Zählstellen.
Das letzte Diagramm zeigt die prozentuale Abdeckung des Netzes. 