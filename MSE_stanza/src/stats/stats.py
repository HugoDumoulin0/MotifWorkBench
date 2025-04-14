# _*_coding:utf-8_*_
import sys
import os
import pandas as pd

import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.conversion import localconverter
from rpy2.robjects.packages import importr

def makehash():
	#~ return collections.defaultdict(makehash)
	return defaultdict(makehash)

class StatsR():
	def __init__(self, rscript):
		self.r = ro.r
		self.importr = importr
		# Load the script file
		self.r.source(rscript)
	
	def pd2R(self, pd_data_obj):
		with localconverter(ro.default_converter + pandas2ri.converter):
			r_data_obj = ro.conversion.py2rpy(pd_data_obj)
		return r_data_obj
		
	def R2pd(self, r_data_obj):
		with localconverter(ro.default_converter + pandas2ri.converter):
			pd_data_obj = ro.conversion.rpy2py(r_data_obj)
		return pd_data_obj
	
