from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but they might need fine-tuning.
build_exe_options = {
    #"excludes": ["tkinter", "unittest"],
    #"zip_include_packages": ["pytchat"],
}

setup(
    name="K's Super TTS",
    version="0.1",
    description="K's TTS for streams and stuff!",
    options={"build_exe": build_exe_options},
    executables=[Executable("../main.py")],
)