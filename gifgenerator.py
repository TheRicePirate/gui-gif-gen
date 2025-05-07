import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import requests
import os
import json
# import pyperclip
from PIL import Image, ImageDraw, ImageFont, ImageSequence, ImageTk
from io import BytesIO
import platform

class GIFDownloaderApp:
    def __init__(self, master):
        self.master = master
        self.master.title("GIF Downloader")
        # Check if configuration file exists
        self.config_file = "config.json"
        if not os.path.exists(self.config_file):
            # If not, create one and ask for API key and client key
            self.create_config()
        else:
            # If exists, load keys from config file
            with open(self.config_file, "r") as f:
                self.config_data = json.load(f)
            self.api_key = self.config_data["api_key"]
            self.client_key = self.config_data["client_key"]
        
        # Initialize variables
        self.gif_urls = []
        self.gif_images = []
        self.selected_index = None
        self.selected_rectangle = None
        
        # Create and place widgets
        self.create_widgets()
        
    def create_widgets(self):
        # Search Term
        self.search_label = tk.Label(self.master, text="Search Term:")
        self.search_label.grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.search_entry = tk.Entry(self.master, width=30)
        self.search_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # Limit
        self.limit_label = tk.Label(self.master, text="Limit:")
        self.limit_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.limit_entry = tk.Entry(self.master, width=30)
        self.limit_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        
        # Top Text
        self.top_text_label = tk.Label(self.master, text="Top Text:")
        self.top_text_label.grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.top_text_entry = tk.Entry(self.master, width=30)
        self.top_text_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        
        # Bottom Text
        self.bottom_text_label = tk.Label(self.master, text="Bottom Text:")
        self.bottom_text_label.grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.bottom_text_entry = tk.Entry(self.master, width=30)
        self.bottom_text_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        
        # Preview Frame
        self.preview_frame = tk.Frame(self.master)
        self.preview_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        self.master.grid_rowconfigure(4, weight=1)  # Allow the preview frame to expand vertically
        
        # Preview Canvas
        self.preview_canvas = tk.Canvas(self.preview_frame, bg="white")
        self.preview_canvas.pack(side="left", fill="both", expand=True)
        
        # Scrollbar
        self.scrollbar = tk.Scrollbar(self.preview_frame, orient="vertical", command=self.preview_canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.preview_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Bind mousewheel event to canvas for scrolling
        self.preview_canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        
        # Download Button
        self.download_button = tk.Button(self.master, text="Download and Add Text", command=self.download_add_text, state=tk.DISABLED)
        self.download_button.grid(row=5, column=0, columnspan=2, pady=10, sticky="ew")
        
        # Retrieve GIFs Button
        self.retrieve_button = tk.Button(self.master, text="Retrieve GIFs", command=self.retrieve_gifs)
        self.retrieve_button.grid(row=6, column=0, columnspan=2, pady=10, sticky="ew")

        # Adjust window size
        self.master.geometry("520x480")  # Set larger window size
        
        # Make all UI elements expand to fill available space
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=1)

    def on_mousewheel(self, event):
        self.preview_canvas.yview_scroll(-1 * int(event.delta/120), "units")

    def create_config(self):
        # Ask for API key and client key
        messagebox.showinfo("Initial Setup", "Please provide your API key and client key.")
        api_key = simpledialog.askstring("API Key", "Enter your API Key:")
        client_key = simpledialog.askstring("Client Key", "Enter your Client Key:")
        
        # Save keys to config file
        with open(self.config_file, "w") as f:
            json.dump({"api_key": api_key, "client_key": client_key}, f)
        
        self.api_key = api_key
        self.client_key = client_key
        
    def retrieve_gifs(self):
        # Clear previous previews
        self.preview_canvas.delete("all")
        
        # Get input values
        search_term = self.search_entry.get()
        limit = int(self.limit_entry.get())
        
        # Call the function to retrieve GIFs
        self.gif_urls = self.get_gif_urls(search_term, limit)
        
        # Load GIF previews
        self.load_gif_previews()
        
        # Enable download button
        self.download_button.config(state=tk.NORMAL)
        
    def get_gif_urls(self, search_term, limit):
        # URL for the Tenor API v2
        url = "https://tenor.googleapis.com/v2/search"
        
        # Parameters for the API request
        params = {
            "q": search_term,
            "key": self.api_key,
            "client_key": self.client_key,
            "limit": limit
        }

        # Sending GET request to the API
        response = requests.get(url, params=params)

        # Checking if the request was successful
        if response.status_code == 200:
            # Extracting JSON data from the response
            data = response.json()

            # Checking if results are present
            results = data.get("results", [])
            if not results:
                messagebox.showinfo("Info", f"No GIFs found for the search term: {search_term}")
                return []

            # Extract and return GIF URLs
            gif_urls = [result["media_formats"]["gif"]["url"] for result in results]
            return gif_urls
        else:
            messagebox.showerror("Error", "Failed to fetch GIFs from Tenor API.")
            return []
        
    def load_gif_previews(self):
        # Clear previous previews
        self.preview_canvas.delete("all")
        
        # Define initial position and row count
        x_offset = 10
        y_offset = 10
        column_count = 0
        
        # Load GIF previews
        for i, url in enumerate(self.gif_urls):
            try:
                response = requests.get(url)
                response.raise_for_status()  # Raise exception for 4xx or 5xx responses
                
                # Load image data
                img_data = BytesIO(response.content)
                img = Image.open(img_data)
                img = img.resize((150, 100), Image.BICUBIC)
                gif_img = ImageTk.PhotoImage(img)
                
                # Add image to list
                self.gif_images.append(gif_img)
                
                # Display image on canvas
                img_id = self.preview_canvas.create_image(x_offset, y_offset, anchor="nw", image=gif_img, tags=f"gif_{i}")
                
                # Bind click event to each GIF preview
                self.preview_canvas.tag_bind(img_id, "<Button-1>", lambda event, index=i: self.on_preview_click(index))
                
                # Update position for next image
                column_count += 1
                if column_count >= 3:  # Maximum columns
                    column_count = 0
                    x_offset = 10
                    y_offset += 120  # Increase y offset to move to next row
                else:
                    x_offset += 160  # Increase x offset to leave space between images
            except Exception as e:
                print(f"Failed to load GIF preview: {e}")
                continue
        
        # Update canvas scrolling region
        self.preview_canvas.config(scrollregion=self.preview_canvas.bbox("all"))

    def on_preview_click(self, index):
        # Remove highlight from previously selected GIF
        if self.selected_rectangle is not None:
            self.preview_canvas.delete(self.selected_rectangle)
        
        # Highlight the clicked GIF with a green rectangle
        self.selected_index = index
        x1, y1, x2, y2 = self.preview_canvas.bbox(f"gif_{index}")
        self.selected_rectangle = self.preview_canvas.create_rectangle(x1, y1, x2, y2, outline="#00FF00", width=3)

    def download_add_text(self):
        if self.selected_index is not None:
            selected_url = self.gif_urls[self.selected_index]
            top_text = self.top_text_entry.get()
            bottom_text = self.bottom_text_entry.get()
            
            # Call function to download and add text to selected GIF
            self.download_and_add_text(selected_url, top_text, bottom_text)
        else:
            messagebox.showinfo("Info", "Please select a GIF to download.")
        
    def download_and_add_text(self, gif_url, top_text, bottom_text):
        try:
            gif_response = requests.get(gif_url)
            gif_response.raise_for_status()  # Raise exception for 4xx or 5xx responses
            
            # Create a file dialog to save the GIF
            filename = filedialog.asksaveasfilename(defaultextension=".gif", filetypes=[("GIF files", "*.gif")])
            
            # Check if a file was selected
            if filename:
                with open(filename, 'wb') as f:
                    f.write(gif_response.content)
                print(f"Downloaded: {filename}")

                # Add text to the GIF
                output = self.add_text_to_gif(filename, top_text, bottom_text)
                if output:
                    with open(filename, 'wb') as f:
                        f.write(output.read())
                    path = filename
                    command = f"powershell Set-Clipboard -LiteralPath {path}"
                    os.system(command)
            
        except Exception as e:
            print(f"Failed to download GIF: {e}")
            messagebox.showerror("Error", f"Failed to download GIF: {e}")

        
    def add_text_to_gif(self, gif_path, top_text, bottom_text):
        try:
            # Load the GIF
            gif = Image.open(gif_path)

            # Create a list to store modified frames
            frames = []

            # Loop through each frame of the GIF
            for frame in ImageSequence.Iterator(gif):
                # Convert frame to RGBA mode
                frame = frame.convert("RGBA")

                # Create a drawing context
                draw = ImageDraw.Draw(frame)

                # Calculate font size based on the frame size
                font_size = max(int(frame.height / 8), 12)  # Adjust the divisor as needed

                # Load the font
                if platform.system() == "Linux":
                    font = ImageFont.truetype("/usr/share/fonts/noto/NotoSans-Regular.ttf", font_size)
                elif platform.system() == "Windows":
                    font = ImageFont.truetype("arial.ttf", font_size)

                # Define text positions
                top_text_position = ((frame.width - draw.textlength(top_text, font=font)) // 2, 20)
                bottom_text_position = ((frame.width - draw.textlength(bottom_text, font=font)) // 2, frame.height / 1.25)

                # Draw black border around top text
                border_width = 2
                border_fill = "black"
                for dx in range(-border_width, border_width + 1):
                    for dy in range(-border_width, border_width + 1):
                        if abs(dx) + abs(dy) != 0:  # Exclude the center position
                            draw.text((top_text_position[0] + dx, top_text_position[1] + dy), top_text, font=font, fill=border_fill)

                # Draw top text
                draw.text(top_text_position, top_text, font=font, fill="white")

                # Draw black border around bottom text
                for dx in range(-border_width, border_width + 1):
                    for dy in range(-border_width, border_width + 1):
                        if abs(dx) + abs(dy) != 0:  # Exclude the center position
                            draw.text((bottom_text_position[0] + dx, bottom_text_position[1] + dy), bottom_text, font=font, fill=border_fill)

                # Draw bottom text
                draw.text(bottom_text_position, bottom_text, font=font, fill="white")

                # Append modified frame to the list
                frames.append(frame)

            # Save the modified frames as an animated GIF
            output = BytesIO()
            frames[0].save(output, format='GIF', save_all=True, append_images=frames[1:], loop=0)
            output.seek(0)

            return output
        except Exception as e:
            print(f"Failed to add text to GIF: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GIFDownloaderApp(root)
    root.mainloop()
