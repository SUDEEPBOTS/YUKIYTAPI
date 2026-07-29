from setuptools import setup, Extension

extensions = [
    Extension("YUKIYTAPI.main", ["YUKIYTAPI/main.c"]),
    Extension("YUKIYTAPI.database.stats", ["YUKIYTAPI/database/stats.c"])
]

setup(
    name="YUKIYTAPI",
    ext_modules=extensions,
)
