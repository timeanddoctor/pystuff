import math

def gravityToPlato(gravity):
  return round((135.997*math.pow(gravity, 3))-(630.272*math.pow(gravity, 2))+(1111.14*gravity)-616.868, 4)

def platoToGravity(plato):
  return round(1+ (plato/(258.6-(227.1*(plato/258.2)))),4)

def celsiusToFahrenheit(celsius):
  fahrenheit = celsius * 9.0/5.0 + 32.00
  return fahrenheit;

def fahrenheitToCelsius(fahrenheit):
  celsius = (fahrenheit-32) * 5.0/9.0
  return celsius;

def computeGravity(sg, temperature, calibration_temperature=15.0, plato=False, celsius=True):
  """
  temperatur is the measured temperature
  """
  if plato:
    sg = platoToGravity(sg);
  if celsius:
    temperature = celsiusToFahrenheit(temperature);
    calibration_temperature = celsiusToFahrenheit(calibration_temperature);

  corrected_gravity = sg * ((1.00130346 - 0.000134722124 * temperature + 0.00000204052596 * (temperature*temperature) - 0.00000000232820948 * (temperature*temperature*temperature)) / (1.00130346 - 0.000134722124 * (calibration_temperature) + 0.00000204052596 * (calibration_temperature*calibration_temperature) - 0.00000000232820948 * (calibration_temperature*calibration_temperature*calibration_temperature)))
  return round(corrected_gravity, 4)

def gravityToReplaceWater(sg, volume, new_sg):
  """
  How much water to replace
  """
  sugar = volume * (sg-1.0)
  new_sugar = (new_sg-1.0) * volume
  keep = volume * new_sugar / sugar
  return volume - keep

def replaceWaterToGravity(sg, volume, replaced):
  """
  Use that 1 g of sugar displace 0.5 ml
  """
  suger = (volume-replaced) * (sg-1.0)
  gravity = suger / (volume + 0.5*sugar) + 1.0
  return gravity

"""

Values are not corrected for sugar displacing water

24.0 grader
1.090 - 38.88
1.085 100  -  38.51 
1.080 100  -  36.63, 36.43, 36.43 = 36.50
1.076 100  -  35.62, 35.60        = 35.61
1.072 100  -  34.39, 34.34, 34.31 = 34.35

23.0 grader

1.070 50   -  33.89, 33.91, 33.92 = 33.91
1.068 50   -  33.33, 33.30        = 33.31
1.066 50   -  32.37, 32.31, 32.30 = 32.33
1.064 50   -  31.87, 31.90, 31.88 = 31.88
1.062 50   -  31.57, 31.55, 31.50 = 31.54
1.060 50   -  31.18, 31.19, 31.20 = 31.19
1.059 50   -  30.83, 30.85, 30.82 = 30.83
1.057 50   -  30.50, 30.54, 30.59 = 30.54
1.054 100  -  29.89, 29.89,       = 29.89
1.051 100  -  29.35, 29.35, 29.35 = 29.35
1.045 200  -  28.17, 28.16        = 28.16
1.040 200  -  27.33, 27.36,       = 27.35
1.034 300  -  26.08, 26.06.       = 26.07
1.028 300  -  25.44, 25.43,       = 25.44
1.023 300  -  24.88, 24.89, 24.88 = 24.88
1.018 400  -  24.18, 24.16, 24.17 = 24.17
1.014 400  -  23.70, 23.72, 23.70 = 23.71

22.0 grader

1.000     22.07, 22.08, 22.09, 

Every gram of sugar displaces 0.5 ml.


 0.9003342867933533 + 0.005008439075709344 *tilt
Degree 2: 0.7393019471433523 + 0.015815080134849994 *tilt-0.00017716269446713654 *tilt*tilt
Degree 3: 0.4432573175595937 + 0.04566777876689018 *tilt-0.00116339178967176 *tilt*tilt + 0.00001068453438881412 *tilt*tilt*tilt

0.8792048981181 + 0.007695678853705*tilt-0.0001376956760855*tilt^2 + 0.0000010082686210055*tilt^3


"""

