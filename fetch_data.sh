#!/bin/sh
# Refresh the NOAA Climate at a Glance CONUS series (nClimDiv, degrees F).
# Update the end year in the URLs as needed.
set -e
mkdir -p data
curl -sL -o data/cag_all_months.csv "https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/national/time-series/110/tavg/all/1/1895-2026/data.csv"
curl -sL -o data/cag_annual.csv     "https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/national/time-series/110/tavg/12/12/1895-2025/data.csv"
tail -2 data/cag_all_months.csv
