import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFilter

class GlassButton(tk.Canvas):
    def __init__(self, master, text="Click Me", width=200, height=60, command=None, **kwargs):
        super().__init__(master, width=width, height=height, highlightthickness=0, bg=master["bg"], **kwargs)
        self.text = text
        self.width = width
        self.height = height
        self.command = command
        
        # State
        self.pressed = False
        
        # Initial render
        self.render()
        
        # Bindings
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", self._on_hover)
        self.bind("<Leave>", self._on_leave)

    def create_glass_image(self, state="normal"):
        # Create a high-res image for the button
        scale = 2
        img_w, img_h = self.width * scale, self.height * scale
        image = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        padding = 10
        rect = [padding, padding, img_w - padding, img_h - padding]
        radius = 30
        
        # Colors based on state
        if state == "pressed":
            bg_color = (255, 255, 255, 40)
            border_color = (255, 255, 255, 100)
            offset = 2
        elif state == "hover":
            bg_color = (255, 255, 255, 80)
            border_color = (255, 255, 255, 180)
            offset = 0
        else:
            bg_color = (255, 255, 255, 60)
            border_color = (255, 255, 255, 150)
            offset = 0

        # Draw Shadow
        shadow = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
        s_draw = ImageDraw.Draw(shadow)
        s_draw.rounded_rectangle(rect, radius=radius, fill=(0, 0, 0, 50))
        shadow = shadow.filter(ImageFilter.GaussianBlur(10))
        image.paste(shadow, (0, 4), shadow)

        # Draw Main Glass Body
        draw.rounded_rectangle(rect, radius=radius, fill=bg_color, outline=border_color, width=2)
        
        # Add Gloss/Highlight (top half)
        highlight = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
        h_draw = ImageDraw.Draw(highlight)
        h_rect = [rect[0], rect[1], rect[2], rect[1] + (rect[3]-rect[1])//2]
        h_draw.rounded_rectangle(h_rect, radius=radius, fill=(255, 255, 255, 40))
        image.paste(highlight, (0, 0), highlight)

        # Resize back to original dimensions
        return image.resize((self.width, self.height), Image.Resampling.LANCZOS)

    def render(self, state="normal"):
        self.delete("all")
        self.img = ImageTk.PhotoImage(self.create_glass_image(state))
        self.create_image(self.width//2, self.height//2, image=self.img)
        
        # Text
        text_color = "white"
        self.create_text(self.width//2, self.height//2, text=self.text, fill=text_color, font=("Arial", 14, "bold"))

    def _on_press(self, event):
        self.pressed = True
        self.render("pressed")
        
    def _on_release(self, event):
        if self.pressed:
            self.pressed = False
            self.render("hover")
            if self.command:
                self.command()

    def _on_hover(self, event):
        if not self.pressed:
            self.render("hover")

    def _on_leave(self, event):
        self.pressed = False
        self.render("normal")

# Example Usage
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Glass 3D Button Demo")
    root.geometry("400x300")
    
    # Set a background image or color to show transparency
    root.configure(bg="#2c3e50")
    
    # Add a colorful background element to show off the glass effect
    canvas = tk.Canvas(root, width=400, height=300, bg="#2c3e50", highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    canvas.create_oval(50, 50, 250, 250, fill="#e74c3c", outline="")
    canvas.create_oval(150, 100, 350, 300, fill="#3498db", outline="")

    def on_click():
        print("Button Clicked!")

    btn = GlassButton(canvas, text="Glass Button", width=180, height=60, command=on_click)
    btn.place(relx=0.5, rely=0.5, anchor="center")

    root.mainloop()
