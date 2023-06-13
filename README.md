# pyportal-flight-tracker
This repository contains the code, libraries, and image assets required to build the PyPortal Flight Tracker. Read a full build tutorial for this project on [Hackster.io](https://www.hackster.io/rhammell/pyportal-flight-tracker-0be6b0).

The Flight Tracker displays real-time flight data on a PyPortal.

A custom map image centered on a user-defined location coordinate is downloaded to the PyPortal and displayed as the background. Every thirty seconds a request is made to the OpenSky Network API for live aircraft data occurring within the map's bounds. Resulting aircraft positions are plotted as icons on the map. 

# Completed Project
<img src="img/flight_tracker.jpg">



