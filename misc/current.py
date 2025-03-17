import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import datetime
import os
import io
import sys
from deepface import DeepFace
import random

faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

class ModernDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Visage Dashboard")
        self.root.geometry("1920x1080")
        root.state("zoomed")
        
        # Store the current image reference at class level
        self.current_image = None
        
        # Theme settings
        self.dark_mode = True
        
        # Colors based on theme
        self.colors = {
            "dark": {
                "bg": "#1E1E2F",
                "card": "#252A41",
                "sidebar": "#171726",
                "text": "#FFFFFF",
                "text_secondary": "#A3A6B4",
                "accent": "#6C5CE7",
                "accent_hover": "#8075E6",
                "success": "#10473F",
                "warning": "#E79C09",
                "danger": "#B30623",
                "border": "#32334D",
                "TableText": "#2d3748"
            },
            "light": {
                "bg": "#E5E0D9",
                "card": "#E5E0D9",
                "sidebar": "#E5E0D9",
                "text": "#2D3748",
                "text_secondary": "#718096",
                "accent": "#2B5288",
                "accent_hover": "#5344D7",
                "success": "#00D084",
                "warning": "#FF9F43",
                "danger": "#FF5E5E",
                "border": "#E2E8F0",
                "TableText": "#2d3748"
            }
        }
        
        # Fonts
        self.fonts = {
            "heading": ("Verdana", 18, "bold"),
            "subheading": ("Verdana", 16, "bold"),
            "body": ("Verdana", 12),
            "small": ("Verdana", 10),
            "body_bold": ("Verdana", 12, "bold"),
            "large_numbers": ("Verdana", 24, "bold")
        }
        
        # Sample data
        self.manager_name = "Arthur Morgan"
        self.employees = [
            {"id": 1, "name": "Sarah Johnson", "position": "Cashier", "performance": "High", "hours": "4/8"},
            {"id": 2, "name": "Michael Smith", "position": "Stocker", "performance": "Medium", "hours": "3/8"},
            {"id": 3, "name": "Emily Davis", "position": "Customer Service", "performance": "High", "hours": "6/8"},
            {"id": 4, "name": "Robert Wilson", "position": "Cashier", "performance": "Low", "hours": "2/8"},
            {"id": 5, "name": "Amanda Lee", "position": "Team Lead", "performance": "High", "hours": "7/8"},
            {"id": 6, "name": "Daniel Miller", "position": "Stocker", "performance": "Medium", "hours": "5/8"},
            {"id": 7, "name": "Olivia White", "position": "Cashier", "performance": "Low", "hours": "1/8"},
            {"id": 8, "name": "James Anderson", "position": "Stocker", "performance": "High", "hours": "8/8"},
            {"id": 9, "name": "Sophia Martinez", "position": "Cashier", "performance": "Medium", "hours": "4/8"},
            {"id": 10, "name": "William Taylor", "position": "Customer Service", "performance": "High", "hours": "6/8"},
            {"id": 11, "name": "Isabella Thomas", "position": "Cashier", "performance": "Low", "hours": "2/8"},
            {"id": 12, "name": "David Hernandez", "position": "Stocker", "performance": "High", "hours": "7/8"},
            {"id": 13, "name": "Mia Moore", "position": "Cashier", "performance": "Medium", "hours": "5/8"},
            {"id": 14, "name": "Benjamin Clark", "position": "Stocker", "performance": "Low", "hours": "1/8"},
            {"id": 15, "name": "Nora Hill", "position": "Cashier", "performance": "High", "hours": "8/8"}
        ]
        
        # Set up the layout
        self.create_base_layout()
        
        # Initialize camera
        self.cap = cv2.VideoCapture(0)
        
        # Start updating elements
        self.update_time()
        self.update_video_feed()
        
    def get_color(self, name):
        """Get color based on current theme"""
        theme = "dark" if self.dark_mode else "light"
        return self.colors[theme][name]
    
    def create_rounded_rectangle(self, width, height, radius=20, fill="#252A41"):
        """Create a rounded rectangle image for backgrounds"""
        rect_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(rect_img)
        
        # Draw rounded rectangle
        draw.rounded_rectangle([(0, 0), (width, height)], radius, fill=fill)
        
        return rect_img
    
    def create_card_bg(self, width, height, radius=20):
        """Create a card background with rounded corners and subtle shadow"""
        # Create base rounded rectangle
        card = self.create_rounded_rectangle(width, height, radius, self.get_color("card"))
        
        # Convert to PhotoImage
        return ImageTk.PhotoImage(card)
    
    def toggle_theme(self):
        """Toggle between dark and light mode"""
        self.dark_mode = not self.dark_mode
        self.refresh_theme()
        
    def refresh_theme(self):
        """Update all UI elements to match current theme"""
        # Update main background
        self.root.configure(bg=self.get_color("bg"))
        
        # Update sidebar
        self.sidebar_frame.configure(bg=self.get_color("sidebar"))
        self.sidebar_header.configure(bg=self.get_color("sidebar"), fg=self.get_color("text"))
        
        for btn in self.sidebar_buttons:
            btn.configure(
                bg=self.get_color("sidebar"),
                fg=self.get_color("text_secondary"),
                activebackground=self.get_color("accent"),
                activeforeground=self.get_color("text")
            )
            
        # Update theme toggle button
        icon = "☀️" if self.dark_mode else "🌙"
        self.theme_btn.configure(text=icon)
        
        # Update content area
        self.content_frame.configure(bg=self.get_color("bg"))
        
        # Update content cards (recreate them)
        for widget in self.main_content.winfo_children():
            widget.destroy()
            
        self.create_dashboard_content()
    
    def create_base_layout(self):
        """Create the basic layout with sidebar and content area"""
        # Configure root
        self.root.configure(bg=self.get_color("bg"))
        
        # Create main container as a grid with 2 columns
        self.main_container = tk.Frame(self.root, bg=self.get_color("bg"))
        self.main_container.pack(fill="both", expand=True)
        
        # 1. Create sidebar (left column)
        sidebar_width = 240
        self.sidebar_frame = tk.Frame(
            self.main_container, 
            width=sidebar_width, 
            bg=self.get_color("sidebar"),
            padx=20,
            pady=20
        )
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)  # Don't shrink
        
        # Sidebar header with app name
        self.sidebar_header = tk.Label(
            self.sidebar_frame, 
            text="Visage", 
            font=self.fonts["heading"],
            bg=self.get_color("sidebar"),
            fg=self.get_color("text"),
            anchor="w",
            pady=15
        )
        self.sidebar_header.pack(fill="x")
        
        # Create navigation buttons with hover effect
        self.sidebar_buttons = []
        
        nav_items = [
            ("📊 Dashboard", self.show_dashboard),
            ("👥 Employees", self.show_dashboard),
            ("📈 Analytics", self.show_dashboard),
            ("⚙️ Settings", self.show_dashboard),
        ]
        
        for text, command in nav_items:
            btn = tk.Button(
                self.sidebar_frame,
                text=text,
                font=self.fonts["body"],
                bg=self.get_color("sidebar"),
                fg=self.get_color("text_secondary"),
                activebackground=self.get_color("accent"),
                activeforeground=self.get_color("text"),
                bd=0,
                cursor="hand2",
                anchor="w",
                padx=10,
                pady=12,
                command=command,
                relief="flat",
                highlightthickness=0
            )
            btn.pack(fill="x", pady=3)
            self.sidebar_buttons.append(btn)
            
            # Bind hover events
            btn.bind("<Enter>", lambda e, b=btn: b.configure(
                bg=self.get_color("accent"), 
                fg=self.get_color("text")
            ))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(
                bg=self.get_color("sidebar"), 
                fg=self.get_color("text_secondary")
            ))
            
        # Add theme toggle at the bottom
        theme_frame = tk.Frame(
            self.sidebar_frame, 
            bg=self.get_color("sidebar"),
            pady=20
        )
        theme_frame.pack(side="bottom", fill="x")
        
        self.theme_btn = tk.Button(
            theme_frame,
            text="☀️",  # Sun icon for dark mode, will change to moon in light mode
            font=("Verdana", 16),
            bg=self.get_color("sidebar"),
            fg=self.get_color("text"),
            bd=0,
            cursor="hand2",
            command=self.toggle_theme,
            activebackground=self.get_color("sidebar"),
            anchor="center"
        )
        self.theme_btn.pack(side="right")
        
        # 2. Create content area (right column)
        self.content_frame = tk.Frame(
            self.main_container, 
            bg=self.get_color("bg"),
            padx=30,
            pady=30
        )
        self.content_frame.pack(side="right", fill="both", expand=True)
        
        # Header with welcome message and date/time
        self.header_frame = tk.Frame(self.content_frame, bg=self.get_color("bg"))
        self.header_frame.pack(fill="x", pady=(0, 20))
        
        # Welcome message
        welcome_frame = tk.Frame(self.header_frame, bg=self.get_color("bg"))
        welcome_frame.pack(side="left", anchor="w")
        
        self.welcome_text = tk.Label(
            welcome_frame,
            text=f"Welcome back, {self.manager_name}",
            font=self.fonts["heading"],
            bg=self.get_color("bg"),
            fg=self.get_color("text")
        )
        self.welcome_text.pack(anchor="w")
        
        self.welcome_subtext = tk.Label(
            welcome_frame,
            text="Here's what's happening with your team today",
            font=self.fonts["body"],
            bg=self.get_color("bg"),
            fg=self.get_color("text_secondary")
        )
        self.welcome_subtext.pack(anchor="w")
        
        # Date and time
        time_frame = tk.Frame(self.header_frame, bg=self.get_color("bg"))
        time_frame.pack(side="right", anchor="e")
        
        self.date_label = tk.Label(
            time_frame,
            font=self.fonts["body"],
            bg=self.get_color("bg"),
            fg=self.get_color("text_secondary")
        )
        self.date_label.pack(anchor="e")
        
        self.time_label = tk.Label(
            time_frame,
            font=self.fonts["heading"],
            bg=self.get_color("bg"),
            fg=self.get_color("text")
        )
        self.time_label.pack(anchor="e")
        
        # Main content area - will be populated by specific views
        self.main_content = tk.Frame(self.content_frame, bg=self.get_color("bg"))
        self.main_content.pack(fill="both", expand=True)
        
        # Show default dashboard view
        self.create_dashboard_content()
    
    def create_dashboard_content(self):
        """Create the dashboard content with metrics, employee list and camera feed"""
        # Create the main grid layout
        self.main_content.columnconfigure(0, weight=3)  # Left column wider
        self.main_content.columnconfigure(1, weight=2)  # Right column narrower
        self.main_content.rowconfigure(0, weight=3)  # Top row for employee list
        self.main_content.rowconfigure(1, weight=1)  # Middle row for KPI metrics
        self.main_content.rowconfigure(2, weight=1)  # Bottom row for emotion chart
        self.main_content.rowconfigure(3, weight=2)  # Bottom row for emotion chart

        
        # 1. Top left: Employee list
        employee_frame = self.create_card_frame("Current Shift Employees")
        employee_frame.grid(row=0, column=0,rowspan=3, sticky="nsew", pady=(0, 10), padx=(0, 10))

        # Employee list content - existing code...
        tree_container = tk.Frame(employee_frame, bg=self.get_color("card"), padx=15, pady=15)
        tree_container.pack(fill="both", expand=True)
        
        # Configure treeview style for the current theme
        style = ttk.Style()
        style.theme_use("clam")  # Use the clam theme as base
        
        # Configure the Treeview widget colors according to our theme
        style.configure(
            "Custom.Treeview",
            background=self.get_color("card"),
            foreground=self.get_color("TableText"),
            fieldbackground=self.get_color("card"),
            rowheight=40
        )
        style.configure(
            "Custom.Treeview.Heading",
            background=self.get_color("bg"),
            foreground=self.get_color("text"),
            font="Verdana 10 bold"
        )
        
        # Set up the tree view with scrollbar
        tree_frame = tk.Frame(tree_container, bg=self.get_color("card"))
        tree_frame.pack(fill="both", expand=True)
        
        self.tree_scroll = tk.Scrollbar(tree_frame, bg=self.get_color("card"))
        self.tree_scroll.pack(side="right", fill="y")
        
        self.employee_tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "Name", "Position", "Performance", "Hours"),
            show="headings",
            style="Custom.Treeview",
            height=5,
            yscrollcommand=self.tree_scroll.set
        )
        
        # Define headings
        self.employee_tree.heading("ID", text="ID")
        self.employee_tree.heading("Name", text="Employee Name")
        self.employee_tree.heading("Position", text="Position")
        self.employee_tree.heading("Performance", text="Performance")
        self.employee_tree.heading("Hours", text="Hours Completed")
        
        # Define columns
        self.employee_tree.column("ID", width=50, anchor="center")
        self.employee_tree.column("Name", width=200, anchor="center")
        self.employee_tree.column("Position", width=150, anchor="center")
        self.employee_tree.column("Performance", width=100, anchor="center")
        self.employee_tree.column("Hours", width=120, anchor="center")
        
        self.employee_tree.pack(side="left", fill="both", expand=True)
        self.tree_scroll.config(command=self.employee_tree.yview)
        
        # Populate employee data
        for employee in self.employees:
            item_id = self.employee_tree.insert("", "end", values=(
                employee["id"], 
                employee["name"], 
                employee["position"], 
                employee["performance"], 
                employee["hours"]
            ))
            
            # Color code based on performance
            if employee["performance"] == "High":
                self.employee_tree.item(item_id, tags=("high",))
            elif employee["performance"] == "Medium":
                self.employee_tree.item(item_id, tags=("medium",))
            elif employee["performance"] == "Low":
                self.employee_tree.item(item_id, tags=("low",))
        
        # Apply color tags - using lighter versions of colors instead of alpha transparency
        def lighten_color(color_hex):
            # Convert hex to RGB and make it lighter
            r = int(color_hex[1:3], 16)
            g = int(color_hex[3:5], 16)
            b = int(color_hex[5:7], 16)
            # Blend with white to create a lighter version (simulating transparency)
            r = r + int((255 - r) * 0.3)  # 80% lighter
            g = g + int((255 - g) * 0.3)
            b = b + int((255 - b) * 0.3)
            return f"#{r:02x}{g:02x}{b:02x}"
            
        self.employee_tree.tag_configure("high", background=lighten_color(self.get_color("success")))
        self.employee_tree.tag_configure("medium", background=lighten_color(self.get_color("warning")))
        self.employee_tree.tag_configure("low", background=lighten_color(self.get_color("danger")))
        
        # 2. Middle left: KPI metrics
        kpi_frame = self.create_card_frame("Team Performance")
        kpi_frame.grid(row=3, column=0, padx=(0, 10), pady=(10, 10), sticky="sew")
    
        # Create metric boxes inside
        metric_grid = tk.Frame(kpi_frame, bg=self.get_color("card"))
        metric_grid.pack(fill="both", expand=True, padx=15, pady=15)
        
        metric_grid.columnconfigure(0, weight=1)
        metric_grid.columnconfigure(1, weight=1)
        metric_grid.columnconfigure(2, weight=1)
        
        metrics = [
            {"title": "Total Employees", "value": str(len(self.employees)), "icon": "👥"},
            {"title": "High Performers", "value": str(sum(1 for e in self.employees if e["performance"] == "High")), "icon": "🌟"},
            {"title": "Low Performers", "value": str(sum(1 for e in self.employees if e["performance"] == "Low")), "icon": "⚠️"}
        ]
        
        for i, metric in enumerate(metrics):
            self.create_metric_box(metric_grid, metric["title"], metric["value"], metric["icon"], i)
            
        # 3. Right column: Camera feed
        camera_frame = self.create_card_frame("Customer Feed")
        camera_frame.grid(row=0, column=1, rowspan=2, padx=(10, 0), pady=(0, 10), sticky="nsew")
        
        self.camera_container = tk.Frame(camera_frame, bg=self.get_color("card"))
        self.camera_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.video_label = tk.Label(self.camera_container, bg="black")
        self.video_label.pack(fill="both", expand=True)
        
        # Emotion display section
        emotion_frame = tk.Frame(self.camera_container, bg=self.get_color("card"), pady=10)
        emotion_frame.pack(fill="x")
        
        emotion_label = tk.Label(
            emotion_frame,
            text="Detected Emotion:",
            font="Verdana 12 bold",
            bg=self.get_color("card"),
            fg=self.get_color("text"),
            anchor="w"
        )
        emotion_label.pack(side="left", padx=(0, 5))
        
        self.emotion_display = tk.Label(
            emotion_frame,
            text="Detecting...",
            font=self.fonts["body_bold"],
            bg=self.get_color("accent"),
            fg=self.get_color("text"),
            padx=15,
            pady=2
        )
        self.emotion_display.pack(side="left", fill="x", expand=True)
        
        # Camera controls
        controls_frame = tk.Frame(self.camera_container, bg=self.get_color("card"), pady=10)
        controls_frame.pack(fill="x")
        '''
        self.screenshot_btn = self.create_button(
            controls_frame, "📷 Take Screenshot", self.take_screenshot,
            bg=self.get_color("accent")
        )
        self.screenshot_btn.pack(side="left", padx=(0, 5), fill="x", expand=True)
        
        self.settings_btn = self.create_button(
            controls_frame, "⚙️ Camera Settings", lambda: None,
            bg=self.get_color("text_secondary")
        )
        self.settings_btn.pack(side="right", padx=(5, 0), fill="x", expand=True)
        '''
        # 4. Bottom left: Emotion chart - Actually call the method now
        self.create_emotion_chart()
    
    def create_emotion_chart(self):
        """Create a simple bar chart showing the top emotions"""
        # Sample emotion data - this would be replaced with real data in production
        self.emotion_stats = [
            {"emotion": "Happy", "percentage": 45},
            {"emotion": "Neutral", "percentage": 25},
            {"emotion": "Surprised", "percentage": 15},
            {"emotion": "Sad", "percentage": 10},
            {"emotion": "Angry", "percentage": 5}
        ]
        
        # Create the card frame for emotions chart
        emotion_chart_frame = self.create_card_frame("Daily Emotion Analytics")
        emotion_chart_frame.grid(row=2, column=1, padx=(10, 10), pady=(10, 10), sticky="sew")
        
        chart_container = tk.Frame(emotion_chart_frame, bg=self.get_color("card"), padx=15, pady=15)
        chart_container.pack(fill="both", expand=True)
        
        # Title for the chart
        title_label = tk.Label(
            chart_container,
            text="Top 5 Customer Emotions Today",
            font=self.fonts["body_bold"],
            bg=self.get_color("card"),
            fg=self.get_color("text"),
            anchor="w",
            pady=5
        )
        title_label.pack(fill="x")
        
        # Emotion color mapping
        emotion_colors = {
            "Happy": self.get_color("success"),
            "Neutral": self.get_color("accent"),
            "Surprised": self.get_color("warning"),
            "Sad": self.get_color("text_secondary"),
            "Angry": self.get_color("danger")
        }
        
        # Create a container for the bars
        bars_frame = tk.Frame(chart_container, bg=self.get_color("card"), pady=10)
        bars_frame.pack(fill="x")
        
        for emotion_data in self.emotion_stats:
            emotion = emotion_data["emotion"]
            percentage = emotion_data["percentage"]
            
            # Container for this emotion bar
            row_frame = tk.Frame(bars_frame, bg=self.get_color("card"), pady=5)
            row_frame.pack(fill="x")
            
            # Label for emotion name
            name_label = tk.Label(
                row_frame, 
                text=emotion,
                width=10,
                font=self.fonts["body"],
                bg=self.get_color("card"),
                fg=self.get_color("text"),
                anchor="w"
            )
            name_label.pack(side="left")
            
            # Frame for the bar
            bar_container = tk.Frame(row_frame, bg=self.get_color("bg"), height=30)
            bar_container.pack(side="left", fill="x", expand=True, padx=10)
            
            # Calculate width based on percentage
            bar_width = int((percentage / 100) * 300)
            
            # The actual bar
            bar = tk.Canvas(
                bar_container,
                width=bar_width,
                height=30,
                bg=emotion_colors.get(emotion, self.get_color("accent")),
                highlightthickness=0
            )
            bar.pack(side="left", anchor="w")
            
            # Percentage label
            pct_label = tk.Label(
                row_frame,
                text=f"{percentage}%",
                font=self.fonts["body_bold"],
                bg=self.get_color("card"),
                fg=self.get_color("text"),
                width=6,
                anchor="e"
            )
            pct_label.pack(side="right")
        
        # Add a refresh button
        refresh_frame = tk.Frame(chart_container, bg=self.get_color("card"), pady=10)
        refresh_frame.pack(fill="x", pady=(10, 0))
        
        refresh_btn = self.create_button(
            refresh_frame, 
            "🔄 Refresh Data", 
            self.refresh_emotion_data,
            bg=self.get_color("accent")
        )
        refresh_btn.pack(side="right")

    def refresh_emotion_data(self):
        """Refresh the emotion statistics (would connect to actual data in production)"""
        # This is just a simulation - in a real app, this would fetch actual data
        emotions = ["Happy", "Neutral", "Surprised", "Sad", "Angry", "Disgusted", "Fearful"]
        total = 100
        
        # Generate random percentages that sum to 100%
        percentages = []
        remaining = total
        for _ in range(len(emotions) - 1):
            if remaining <= 0:
                percentages.append(0)
            else:
                p = random.randint(0, remaining)
                percentages.append(p)
                remaining -= p
        percentages.append(remaining)
        
        # Shuffle to randomize
        random.shuffle(percentages)
        
        # Create emotion stats and sort by percentage
        stats = [{"emotion": e, "percentage": p} for e, p in zip(emotions, percentages)]
        stats.sort(key=lambda x: x["percentage"], reverse=True)
        
        # Take top 5
        self.emotion_stats = stats[:5]
        
        # Recreate the chart
        for widget in self.main_content.winfo_children():
            widget.destroy()
        
        self.create_dashboard_content()
    
    
    
    def create_card_frame(self, title):
        """Create a card-like frame with title"""
        card_frame = tk.Frame(
            self.main_content,
            bg=self.get_color("card"),
            highlightbackground=self.get_color("border"),
            highlightthickness=1,
            bd=0
        )
        
        # Round corners using the highlightbackground trick
        # (not perfect but best we can do without custom drawing)
        
        # Title
        title_label = tk.Label(
            card_frame,
            text=title,
            font=self.fonts["subheading"],
            bg=self.get_color("card"),
            fg=self.get_color("text"),
            anchor="w",
            pady=15,
            padx=15
        )
        title_label.pack(fill="x")
        
        # Add separator
        separator = tk.Frame(
            card_frame,
            height=1,
            bg=self.get_color("border")
        )
        separator.pack(fill="x")
        
        return card_frame
    
    def create_button(self, parent, text, command, bg=None):
        if bg is None:
            bg = self.get_color("accent")
            
        btn = tk.Button(
            parent,
            text=text,
            font=self.fonts["body"],
            bg=bg,
            fg=self.get_color("text"),
            activebackground=self.get_color("accent_hover"),
            activeforeground=self.get_color("text"),
            bd=0,
            cursor="hand2",
            padx=15,
            pady=8,
            command=command,
            relief="flat"
        )
        
        # Add hover effect
        btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=self.get_color("accent_hover")))
        btn.bind("<Leave>", lambda e, b=btn, orig_bg=bg: b.configure(bg=orig_bg))
        
        return btn
    
    def create_metric_box(self, parent, title, value, icon, col):
        metric_frame = tk.Frame(
            parent,
            bg=self.get_color("card"),
            padx=15,
            pady=15
        )
        metric_frame.grid(row=0, column=col, sticky="nsew", padx=5)
        
        # Icon and title in same row
        header_frame = tk.Frame(metric_frame, bg=self.get_color("card"))
        header_frame.pack(fill="x", anchor="w")
        
        # Icon (emoji)
        icon_label = tk.Label(
            header_frame,
            text=icon,
            font=("Verdana", 20),
            bg=self.get_color("card"),
            fg=self.get_color("text")
        )
        icon_label.pack(side="left", anchor="w")
        
        title_label = tk.Label(
            header_frame,
            text=title,
            font=self.fonts["body"],
            bg=self.get_color("card"),
            fg=self.get_color("text_secondary"),
            padx=10
        )
        title_label.pack(side="left", anchor="w")
        
        # Value
        value_label = tk.Label(
            metric_frame,
            text=value,
            font=self.fonts["large_numbers"],
            bg=self.get_color("card"),
            fg=self.get_color("text"),
            pady=10
        )
        value_label.pack(anchor="w")
    
    def update_time(self):
        """Update date and time labels"""
        now = datetime.datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        time_str = now.strftime("%H:%M:%S")
        
        self.date_label.config(text=date_str)
        self.time_label.config(text=time_str)
    
    def update_video_feed(self):
        """Update the video feed from the webcam"""
        try:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    # Resize the frame to fit our layout
                    frame = cv2.resize(frame, (400, 300))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)
                    self.current_image = ImageTk.PhotoImage(image=img)
                    self.video_label.config(image=self.current_image)
                    # Keep a reference to prevent garbage collection
                    self.video_label.image = self.current_image
                    self.update_time()
                    # Convert frame to grayscale for face detection
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    
                    # Detect faces in the frame
                    faces = faceCascade.detectMultiScale(gray, 1.1, 4)

                    # Perform emotion analysis
                    try:
                        result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
                        print(result)
                    except Exception as e:
                        print(f"Error during face analysis: {str(e)}")
                        result = None

                    random_var = random.randint(0, 4)

                    # Extract dominant emotion if analysis is successful
                    if isinstance(result, dict) and 'dominant_emotion' in result:
                        dominant_emotion = result['dominant_emotion']
                        
                        # Update emotion display in UI
                        
                        if random_var == 0:
                            self.emotion_display.config(text=dominant_emotion.capitalize())
                            # Set background color based on emotion
                            if dominant_emotion in ["happy", "surprise"]:
                                color = self.get_color("success")
                            elif dominant_emotion in ["angry", "disgust", "fear"]:
                                color = self.get_color("danger")
                            else:  # neutral, sad
                                color = self.get_color("warning")
                        
                            self.emotion_display.config(bg=color)
                            
                            
                    else:
                        # No emotion detected
                        self.emotion_display.config(text="No emotion detected", bg=self.get_color("text_secondary"))
                else:
                    # Handle camera read failure
                    print("Failed to read frame from camera")
            else:
                # Try to reinitialize the camera if it's closed
                print("Camera not open, attempting to reopen...")
                self.cap = cv2.VideoCapture(0)
        except Exception as e:
            print(f"Error in video feed: {e}")
        
        # Schedule the next update
        self.root.after(30, self.update_video_feed)
    
    def take_screenshot(self):
        """Demo function for screenshot button"""
        print("Screenshot taken")

    def show_dashboard(self):
        """Show the dashboard view (already implemented)"""
        pass  # We're already showing it
    
    def on_closing(self):
        """Handle application closing"""
        if self.cap.isOpened():
            self.cap.release()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernDashboard(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()