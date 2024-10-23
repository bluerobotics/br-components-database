import kiutils.symbol
import os
import glob
import pandas as pd

PARTS_SHEET_PATH = "C:/Users/JacobBrotmanKrass/Documents/GitHub/br-components-database/Kicad/Parts_Library.xlsx"
parts_sheet = pd.read_excel(PARTS_SHEET_PATH, index_col=[0])

