import tkinter as tk
import json


def show_approval_popup(tool_name: str, arguments: dict):
    root = tk.Tk()

    window_width = 480
    window_height = 500

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    
    root.title("MCP Guardian — Security Approval")
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    root.resizable(False, False)
    root.attributes("-topmost", True)
    root.configure(bg="#111827")

    decision = None

    # ---------- Button actions ----------
    def allow_request():
        nonlocal decision
        decision = "approved"
        root.destroy()

    def block_request():
        nonlocal decision
        decision = "blocked"
        root.destroy()

    # ---------- Header ----------
    header = tk.Frame(root, bg="#1F2937", height=75)
    header.pack(fill="x")
    header.pack_propagate(False)

    title = tk.Label(
        header,
        text="MCP GUARDIAN",
        font=("Arial", 16, "bold"),
        fg="#F9FAFB",
        bg="#1F2937",
    )
    title.pack(anchor="w", padx=20, pady=(15, 0))

    subtitle = tk.Label(
        header,
        text="SECURITY APPROVAL REQUIRED",
        font=("Arial", 9, "bold"),
        fg="#F59E0B",
        bg="#1F2937",
    )
    subtitle.pack(anchor="w", padx=22, pady=(3, 10))

    # ---------- Warning ----------
    warning = tk.Label(
        root,
        text="A tool is requesting permission to execute",
        font=("Arial", 10),
        fg="#FBBF24",
        bg="#111827",
    )
    warning.pack(pady=(20, 15))

    # ---------- Tool card ----------
    tool_card = tk.Frame(
        root,
        bg="#1F2937",
        highlightbackground="#374151",
        highlightthickness=1,
    )
    tool_card.pack(fill="x", padx=20)

    tool_heading = tk.Label(
        tool_card,
        text="TOOL",
        font=("Arial", 9, "bold"),
        fg="#9CA3AF",
        bg="#1F2937",
    )
    tool_heading.pack(anchor="w", padx=15, pady=(12, 5))

    tool_label = tk.Label(
        tool_card,
        text=tool_name,
        font=("Consolas", 13, "bold"),
        fg="#60A5FA",
        bg="#1F2937",
        anchor="w",
    )
    tool_label.pack(anchor="w", padx=15, pady=(0, 12))

    # ---------- Arguments card ----------
    args_card = tk.Frame(
        root,
        bg="#1F2937",
        highlightbackground="#374151",
        highlightthickness=1,
    )
    args_card.pack(fill="x", padx=20, pady=12)

    args_heading = tk.Label(
        args_card,
        text="ARGUMENTS",
        font=("Arial", 9, "bold"),
        fg="#9CA3AF",
        bg="#1F2937",
    )
    args_heading.pack(anchor="w", padx=15, pady=(8, 3))

    # Convert arguments into formatted JSON.
    args_text = json.dumps(
        arguments,
        indent=2,
        ensure_ascii=False,
    )

    if not args_text:
        args_text = "No arguments provided"

    args_display = tk.Text(
        args_card,
        height=4,
        font=("Consolas", 10),
        fg="#D1D5DB",
        bg="#111827",
        insertbackground="#D1D5DB",
        relief="flat",
        wrap="none",
        padx=10,
        pady=8,
    )

    args_display.insert("1.0", args_text)
    args_display.config(state="disabled")

    args_display.pack(fill="x", padx=15, pady=(0, 5))

    # ---------- Warning note ----------
    note = tk.Label(
        root,
        text="This request will execute on the MCP server if allowed.",
        font=("Arial", 9),
        fg="#9CA3AF",
        bg="#111827",
    )
    note.pack(pady=(2, 15))

    # ---------- Buttons ----------
    button_frame = tk.Frame(root, bg="#111827")
    button_frame.pack(fill="x", padx=20)

    block_button = tk.Button(
        button_frame,
        text="BLOCK",
        command=block_request,
        font=("Arial", 10, "bold"),
        fg="white",
        bg="#DC2626",
        activebackground="#B91C1C",
        activeforeground="white",
        relief="flat",
        cursor="hand2",
        height=2,
    )
    block_button.pack(side="left", expand=True, fill="x", padx=(0, 8))

    allow_button = tk.Button(
        button_frame,
        text="ALLOW",
        command=allow_request,
        font=("Arial", 10, "bold"),
        fg="white",
        bg="#16A34A",
        activebackground="#15803D",
        activeforeground="white",
        relief="flat",
        cursor="hand2",
        height=2,
    )
    allow_button.pack(side="right", expand=True, fill="x", padx=(8, 0))

    root.mainloop()

    return decision


if __name__ == "__main__":
    result = show_approval_popup(
        tool_name="calculate_sum",
        arguments={
            "a": 10,
            "b": 20,
        },
    )

    print(f"User decision: {result}")