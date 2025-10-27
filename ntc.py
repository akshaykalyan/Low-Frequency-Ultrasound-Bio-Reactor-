
from gpiozero import MCP3208
import numpy as np

red_pot = MCP3208(channel=1)
a1=0.003354016
b1=0.000256524
c1=2.60597E-06
d1=6.32926E-08
r25 = 10000

def kelvin_to_celsius(k):
	return k - 273.15

while(True):
	adc_value = red_pot.value*3.3
	r= (adc_value*r25)/(3.3-adc_value)
	t_in_k= 1/(a1+b1*np.log(r/r25)+c1*(np.log(r/r25)**2)+d1*(np.log(r/r25)**3))
	print(r,keZ)