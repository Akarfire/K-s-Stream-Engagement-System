import customtkinter
import socket

Host = "127.0.0.1"
Port = 22222

Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
Socket.connect((Host, Port))

def SendTask(InTask):
    Socket.sendall(InTask)
    Resp = Socket.recv(1024)
    print(f"Response: {Resp!r}")

customtkinter.set_appearance_mode("System")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

app = customtkinter.CTk()  # create CTk window like you do with the Tk window
app.title("Control Panel")
app.geometry("410x400")

TextBox = customtkinter.CTkTextbox(app, width=200, height=100)
TextBox.grid(row=0, column=0)
TextBox.place(relx=0.5, rely=0.05, anchor=customtkinter.N)

def ConfirmButton():

    Text = TextBox.get("0.0", "end")
    TextBox.delete("0.0", "end")

    if len(Text) > 0:
        SendTask(Text.encode("utf-8"))


# Use CTkButton instead of tkinter Button
button = customtkinter.CTkButton(master=app, text="Confirm", command=ConfirmButton)
button.place(relx=0.5, rely=0.35, anchor=customtkinter.N)


app.mainloop()
