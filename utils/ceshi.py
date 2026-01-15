import replicate
import os

ss = "r8_IjJ85Orrr3DsLZhXm24eVLgbLWAyeio2Asc4o"
os.environ['REPLICATE_API_TOKEN'] = ss

output = replicate.run(
    "black-forest-labs/flux-pro",
    input={
        "prompt": "an abstract painting of a sunrise"
    }
)
print(output.)
