import customtkinter
import socket

host = "127.0.0.1"
port = 22222

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect((host, port))

def SendTask(InTask):
    socket.sendall(InTask)
    resp = socket.recv(1024)
    print(f"Response: {resp!r}")

customtkinter.set_appearance_mode("System")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

app = customtkinter.CTk()  # create CTk window like you do with the Tk window
app.title("Control Panel")
app.geometry("410x230")

text_box= customtkinter.CTkTextbox(app, width=200, height=100)
text_box.grid(row=0, column=0)
text_box.place(relx=0.5, rely=0.05, anchor=customtkinter.N)

def ConfirmButton():

    text = text_box.get("0.0", "end")
    text_box.delete("0.0", "end")

    if len(text) > 0:
        SendTask(text.encode("utf-8"))

def SpamModeButton():

    text = "!SPAM_EV!"
    SendTask(text.encode("utf-8"))


# Use CTkButton instead of tkinter Button
confirm_button = customtkinter.CTkButton(master=app, text="Confirm", command=ConfirmButton)
confirm_button.place(relx=0.5, rely=0.75, anchor=customtkinter.S)

spam_mode_button = customtkinter.CTkButton(master=app, text="Spam Mode", command=SpamModeButton)
spam_mode_button.place(relx=0.5, rely=0.9, anchor=customtkinter.S)

app.mainloop()
