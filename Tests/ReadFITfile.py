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