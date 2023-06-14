# Script to test the import of a .fit file using the Garmin sdk
from garmin_fit_sdk import Decoder, Stream, Profile
from Utilities.dataPath import getDataPath
import numpy as np
import pandas as pd
import seaborn as sns

filePath = getDataPath() + "\\11329404102_ACTIVITY.fit"
print(filePath)

stream = Stream.from_file(filePath)
decoder = Decoder(stream)
messages, errors = decoder.read()

print(errors)
#print(messages)

# Decode messages into usable format
df = pd.DataFrame(messages['record_mesgs'])
df.drop(columns=136, inplace=True) # Drops 136 because it is exactly the heart rate
df.drop(columns=135, inplace=True) # Drops 135 because no clue what it actually is
df['cadence_spm'] = (df['cadence'] + df['fractional_cadence'])*2 # Get cadence in Steps per minute - https://forums.garmin.com/developer/fit-sdk/f/discussion/288454/fractional-cadence-values
df['position_lat_deg'] = df['position_lat'] * ( 180 / 2**31 ) # Get position in deg - https://forums.garmin.com/developer/fit-sdk/f/discussion/280125/record-the-latitude-and-longitude-format-of-the-message
df['position_long_deg'] = df['position_long'] * ( 180 / 2**31 )
