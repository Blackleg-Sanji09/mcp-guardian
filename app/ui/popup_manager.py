import asyncio
import threading
import queue
import tkinter as tk

from app.ui.approval_popup import show_approval_popup


class PopupManager:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.request_queue = queue.Queue()

        self.active_popups = 0
        self.popup_offset = 40

        self.gui_thread = threading.Thread(
            target=self._run_gui,
            daemon=True,
        )
        self.gui_thread.start()

    def show_popup(
        self,
        request_id: str,
        tool_name: str,
        arguments: dict,
        approval_manager,
    ):
        self.request_queue.put(
            (
                request_id,
                tool_name,
                arguments,
                approval_manager,
            )
        )

    def _run_gui(self):
        self.root = tk.Tk()
        self.root.withdraw()

        self.root.after(100, self._process_queue)
        self.root.mainloop()

    def _get_popup_position(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        window_width = 480
        window_height = 500

        # Arrange popups diagonally.
        offset = self.active_popups * self.popup_offset

        x = (screen_width - window_width) // 2 + offset
        y = (screen_height - window_height) // 2 + offset

        # Keep popups within the screen.
        x = min(max(x, 0), screen_width - window_width)
        y = min(max(y, 0), screen_height - window_height)

        return x, y

    def _process_queue(self):
        while not self.request_queue.empty():
            try:
                (
                    request_id,
                    tool_name,
                    arguments,
                    approval_manager,
                ) = self.request_queue.get_nowait()

            except queue.Empty:
                break

            self.active_popups += 1

            def handle_decision(
                decision,
                request_id=request_id,
                approval_manager=approval_manager,
            ):
                if decision == "approved":
                    self.loop.call_soon_threadsafe(
                        approval_manager.approve_request,
                        request_id,
                    )

                elif decision == "blocked":
                    self.loop.call_soon_threadsafe(
                        approval_manager.block_request,
                        request_id,
                    )

                self.active_popups = max(
                    0,
                    self.active_popups - 1,
                )

            show_approval_popup(
                parent=self.root,
                tool_name=tool_name,
                arguments=arguments,
                on_decision=handle_decision,
                position=self._get_popup_position(),
            )

        # Continue checking for new requests.
        self.root.after(100, self._process_queue)